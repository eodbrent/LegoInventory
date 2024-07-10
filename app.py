from flask import Flask, render_template, jsonify, request
import requests
import json
import os
from datetime import datetime
import configparser

app = Flask(__name__)

config_file = 'config.ini'

def handle_response(response):
    response_codes = {
        200: "OK: The request was successful.",
        400: "Bad Request: The request was invalid or cannot be served.",
        401: "Unauthorized: The request requires user authentication.",
        403: "Forbidden: The server understood the request, but is refusing it.",
        404: "Not Found: There is no resource behind the URI.",
        500: "Internal Server Error: The server met an unexpected condition."
    }
    return response_codes.get(response.status_code, "Unknown Error")

def save_data_to_file(data):
    filename = "601_sets.txt"
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            existing_data = json.load(file)
        for new_item in data.get('results', []):
            for existing_item in existing_data.get('results', []):
                if new_item['set_num'] == existing_item['set_num']:
                    new_item['owned'] = existing_item.get('owned', False)
                    new_item['built'] = existing_item.get('built', False)
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    return filename

def download_images(data):
    current_dir = os.path.abspath(os.path.dirname(__file__))
    image_dir = os.path.join(current_dir, "static", "images")

    print(f"Image directory: {image_dir}")

    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
        print(f"Created directory: {image_dir}")

    results = data.get('results', [])
    for item in results:
        img_url = item.get('set_img_url')
        img_name = os.path.join(image_dir, f"{item['set_num']}.jpg")

        print(f"Image URL: {img_url}, Image name: {img_name}")

        if img_url and not os.path.exists(img_name):
            try:
                img_response = requests.get(img_url)
                if img_response.status_code == 200:
                    img_data = img_response.content
                    with open(img_name, 'wb') as img_file:
                        img_file.write(img_data)
                    print(f"Downloaded image: {img_name}")
            except Exception as e:
                print(f"Failed to download image {img_url}: {e}")

def update_last_retrieved():
    config = configparser.ConfigParser()
    config.read(config_file)
    if 'DEFAULT' not in config:
        config['DEFAULT'] = {}
    config['DEFAULT']['last_retrieved'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(config_file, 'w') as configfile:
        config.write(configfile)

def load_last_retrieved():
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['DEFAULT'].get('last_retrieved', 'Initial retrieve required')

@app.route('/')
def index():
    last_retrieved = load_last_retrieved()
    sets = []
    if os.path.exists("601_sets.txt"):
        with open("601_sets.txt", 'r') as file:
            data = json.load(file)
            sets = data.get('results', [])
    return render_template('index.html', last_retrieved=last_retrieved, sets=sets)

@app.route('/retrieve')
def retrieve_action():
    url = "https://rebrickable.com/api/v3/lego/sets/?theme_id=601&key=07be16f230dbdc82027005ff9340116d"
    response = requests.get(url)
    status_message = handle_response(response)
    if response.status_code == 200:
        data = response.json()
        save_data_to_file(data)
        download_images(data)
        update_last_retrieved()
        return jsonify({"status": "success", "message": "Data retrieved and saved successfully!"})
    else:
        return jsonify({"status": "error", "message": f"Error {response.status_code}: {status_message}"})

@app.route('/filter', methods=['POST'])
def filter_sets():
    if os.path.exists("601_sets.txt"):
        with open("601_sets.txt", 'r') as file:
            data = json.load(file)
        results = data.get('results', [])

        filter_not_owned = 'filter_not_owned' in request.form
        filter_not_built = 'filter_not_built' in request.form

        if filter_not_owned:
            results = [set for set in results if not set.get('owned', False)]
        if filter_not_built:
            results = [set for set in results if not set.get('built', False)]

        return jsonify({"sets": results})
    return jsonify({"sets": []})

if __name__ == '__main__':
    app.run(debug=True)
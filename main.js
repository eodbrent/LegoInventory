const { app, BrowserWindow } = require('electron');
const path = require('path');
const { exec } = require('child_process');

let flaskProcess;

function createWindow () {
    const mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true
        }
    });

    // Start the Flask app
    flaskProcess = exec('python "G:\\My Drive\\Python\\Lego Web\\app.py"', (err, stdout, stderr) => {
        if (err) {
            console.error(`exec error: ${err}`);
            return;
        }
        console.log(`stdout: ${stdout}`);
        console.error(`stderr: ${stderr}`);
    });

    // Load the Flask app URL in the Electron window
    mainWindow.loadURL('http://localhost:5000');

    mainWindow.on('closed', function () {
        if (flaskProcess) {
            flaskProcess.kill();  // Ensure Flask process is killed when Electron window is closed
        }
        app.quit();
    });
}

app.on('ready', createWindow);

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
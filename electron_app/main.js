const { app, BrowserWindow } = require('electron');
const path = require('path');
const http = require('http');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    title: "OmniTwin AGI Interface",
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  // Wait for the Next.js frontend to boot before loading the URL
  const checkServer = () => {
    http.get('http://localhost:3000', (res) => {
      if (res.statusCode === 200) {
        win.loadURL('http://localhost:3000');
      } else {
        setTimeout(checkServer, 1000);
      }
    }).on('error', () => {
      setTimeout(checkServer, 1000);
    });
  };

  // Initially load a splash screen while the backend cluster boots
  win.loadFile('splash.html');
  checkServer();
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // In a full build, this would also trigger a teardown of the docker cluster
    app.quit();
  }
});

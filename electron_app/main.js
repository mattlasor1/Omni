const { app, BrowserWindow } = require("electron");
const fs = require("fs");
const http = require("http");
const path = require("path");
const { spawn } = require("child_process");

const projectRoot = path.resolve(__dirname, "..");
const frontendDir = path.join(projectRoot, "frontend");
const isWindows = process.platform === "win32";
const npmCommand = isWindows ? "npm.cmd" : "npm";

let backendProcess = null;
let frontendProcess = null;

function resolvePython() {
  const venvPython = isWindows
    ? path.join(projectRoot, ".venv", "Scripts", "python.exe")
    : path.join(projectRoot, ".venv", "bin", "python");
  return fs.existsSync(venvPython) ? venvPython : "python";
}

function spawnService(command, args, cwd, extraEnv = {}) {
  return spawn(command, args, {
    cwd,
    env: { ...process.env, ...extraEnv },
    shell: false,
    stdio: "ignore",
  });
}

function startBackend() {
  if (backendProcess) {
    return;
  }
  backendProcess = spawnService(
    resolvePython(),
    ["-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"],
    projectRoot
  );
}

function startFrontend() {
  if (frontendProcess) {
    return;
  }
  const hasBuild = fs.existsSync(path.join(frontendDir, ".next", "BUILD_ID"));
  frontendProcess = spawnService(
    npmCommand,
    ["run", hasBuild ? "start" : "dev"],
    frontendDir,
    { HOSTNAME: "127.0.0.1", PORT: "3000" }
  );
}

function stopService(child) {
  if (child && !child.killed) {
    child.kill();
  }
}

function waitForServer(url, onReady) {
  const check = () => {
    http
      .get(url, (res) => {
        if (res.statusCode === 200) {
          onReady();
        } else {
          setTimeout(check, 1000);
        }
      })
      .on("error", () => setTimeout(check, 1000));
  };
  check();
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 860,
    title: "OmniTwin Offline Workbench",
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  win.loadFile("splash.html");
  waitForServer("http://127.0.0.1:3000", () => win.loadURL("http://127.0.0.1:3000"));
}

app.whenReady().then(() => {
  startBackend();
  startFrontend();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("before-quit", () => {
  stopService(frontendProcess);
  stopService(backendProcess);
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

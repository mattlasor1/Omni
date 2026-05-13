const { app, BrowserWindow, session } = require("electron");
const fs = require("fs");
const http = require("http");
const path = require("path");
const { spawn } = require("child_process");

const projectRoot = app.isPackaged ? process.resourcesPath : path.resolve(__dirname, "..");
const frontendDir = app.isPackaged ? path.join(projectRoot, "out") : path.join(projectRoot, "frontend");
const logDir = path.join(projectRoot, "data", "logs");
const isWindows = process.platform === "win32";
const npmCommand = isWindows ? "npm.cmd" : "npm";

let backendProcess = null;
let frontendProcess = null;
let staticFrontendServer = null;
let mainWindow = null;
let backendReady = false;
let frontendReady = false;
let startupFailed = false;

const logs = {
  backend: "",
  frontend: "",
};

const offlineEnv = {
  OMNI_OFFLINE_STRICT: "true",
  OMNI_ENABLE_MODEL_DOWNLOADS: "false",
  OMNI_ENABLE_SWARM: "false",
  OMNI_ALLOW_LAN: "false",
  OMNI_ENABLE_EXTERNAL_DEVICES: "false",
  HF_HUB_OFFLINE: "1",
  TRANSFORMERS_OFFLINE: "1",
  HF_DATASETS_OFFLINE: "1",
  NEXT_TELEMETRY_DISABLED: "1",
};

function ensureLogDir() {
  fs.mkdirSync(logDir, { recursive: true });
}

function resolvePython() {
  const venvPython = isWindows
    ? path.join(projectRoot, ".venv", "Scripts", "python.exe")
    : path.join(projectRoot, ".venv", "bin", "python");
  return fs.existsSync(venvPython) ? venvPython : "python";
}

function appendLog(name, chunk) {
  const text = chunk.toString();
  logs[name] = `${logs[name]}${text}`.slice(-12000);
  fs.appendFileSync(path.join(logDir, `${name}.log`), text);
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function isLocalUrl(rawUrl) {
  try {
    const parsed = new URL(rawUrl);
    if (["file:", "data:", "devtools:"].includes(parsed.protocol)) {
      return true;
    }
    return ["localhost", "127.0.0.1", "::1", "[::1]"].includes(parsed.hostname);
  } catch (_) {
    return false;
  }
}

function installElectronNetworkGuard() {
  const filter = { urls: ["http://*/*", "https://*/*", "ws://*/*", "wss://*/*"] };
  session.defaultSession.webRequest.onBeforeRequest(filter, (details, callback) => {
    callback({ cancel: !isLocalUrl(details.url) });
  });
}

function updateSplash(status, detail = "") {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }
  const payload = JSON.stringify({ status, detail });
  mainWindow.webContents
    .executeJavaScript(
      `(() => {
        const payload = ${payload};
        const statusEl = document.getElementById("status");
        const detailEl = document.getElementById("detail");
        if (statusEl) statusEl.textContent = payload.status;
        if (detailEl) detailEl.textContent = payload.detail;
      })();`,
      true
    )
    .catch(() => {});
}

function showFailure(serviceName, detail) {
  startupFailed = true;
  const backendLog = escapeHtml(logs.backend || "No backend logs captured.");
  const frontendLog = escapeHtml(logs.frontend || "No frontend logs captured.");
  const html = `
    <html>
      <head>
        <title>OmniTwin Startup Failure</title>
        <style>
          body { font-family: Segoe UI, Arial, sans-serif; background: #111827; color: #e5e7eb; padding: 24px; }
          h1 { margin-top: 0; color: #f87171; }
          pre { background: #0b1220; padding: 12px; border-radius: 8px; white-space: pre-wrap; overflow-wrap: anywhere; }
          .section { margin-top: 18px; }
        </style>
      </head>
      <body>
        <h1>${escapeHtml(serviceName)} failed to start</h1>
        <p>${escapeHtml(detail)}</p>
        <p>Logs were written to ${escapeHtml(logDir)}.</p>
        <div class="section">
          <strong>Backend log tail</strong>
          <pre>${backendLog}</pre>
        </div>
        <div class="section">
          <strong>Frontend log tail</strong>
          <pre>${frontendLog}</pre>
        </div>
      </body>
    </html>
  `;
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  }
}

function monitorProcess(child, name, onFailure) {
  child.stdout?.on("data", (chunk) => appendLog(name, chunk));
  child.stderr?.on("data", (chunk) => appendLog(name, chunk));
  child.on("error", (error) => onFailure(`${name} process error: ${error.message}`));
  child.on("exit", (code) => {
    const ready = name === "backend" ? backendReady : frontendReady;
    if (!ready && !startupFailed) {
      onFailure(`${name} exited before startup completed (code ${code ?? "unknown"}).`);
    }
  });
}

function spawnService(command, args, cwd, name) {
  const child = spawn(command, args, {
    cwd,
    env: { ...process.env, ...offlineEnv },
    shell: false,
    stdio: ["ignore", "pipe", "pipe"],
  });
  monitorProcess(child, name, (message) => showFailure(name, message));
  return child;
}

function requestJson(url) {
  return new Promise((resolve, reject) => {
    http
      .get(url, (res) => {
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          try {
            resolve({ statusCode: res.statusCode, body: body ? JSON.parse(body) : {} });
          } catch (error) {
            reject(error);
          }
        });
      })
      .on("error", reject);
  });
}

function requestStatus(url) {
  return new Promise((resolve, reject) => {
    http
      .get(url, (res) => resolve(res.statusCode))
      .on("error", reject);
  });
}

function contentTypeFor(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  const types = {
    ".css": "text/css",
    ".html": "text/html",
    ".ico": "image/x-icon",
    ".js": "application/javascript",
    ".json": "application/json",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain",
    ".webp": "image/webp",
  };
  return types[extension] || "application/octet-stream";
}

function startStaticFrontendServer(rootDir) {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(path.join(rootDir, "index.html"))) {
      reject(new Error(`Static frontend bundle not found at ${rootDir}. Run npm run build in frontend first.`));
      return;
    }

    staticFrontendServer = http.createServer((req, res) => {
      const requestUrl = new URL(req.url || "/", "http://127.0.0.1:3000");
      const decodedPath = decodeURIComponent(requestUrl.pathname);
      const safeRoot = path.resolve(rootDir);
      const normalizedPath = path.normalize(decodedPath).replace(/^[/\\]+/, "");
      let filePath = path.resolve(safeRoot, normalizedPath);
      if (filePath !== safeRoot && !filePath.startsWith(`${safeRoot}${path.sep}`)) {
        res.writeHead(403);
        res.end("Forbidden");
        return;
      }
      if (decodedPath === "/" || !fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = path.join(safeRoot, "index.html");
      }
      fs.readFile(filePath, (error, data) => {
        if (error) {
          res.writeHead(404);
          res.end("Not found");
          return;
        }
        res.writeHead(200, { "Content-Type": contentTypeFor(filePath) });
        res.end(data);
      });
    });

    staticFrontendServer.once("error", reject);
    staticFrontendServer.listen(3000, "127.0.0.1", () => resolve());
  });
}

async function waitForServer(check, timeoutMs, serviceName) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (startupFailed) {
      throw new Error(`${serviceName} startup aborted.`);
    }
    try {
      const ok = await check();
      if (ok) {
        return;
      }
    } catch (_) {}
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`${serviceName} did not become ready within ${timeoutMs / 1000} seconds.`);
}

function stopService(child) {
  if (child && !child.killed) {
    child.kill();
  }
}

function stopStaticFrontend() {
  if (staticFrontendServer) {
    staticFrontendServer.close();
    staticFrontendServer = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    title: "OmniTwin Offline Workbench",
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });
  mainWindow.loadFile("splash.html");
}

async function bootstrapDesktop() {
  try {
    updateSplash("Starting backend", "Booting FastAPI and local maintenance runtime...");
    backendProcess = spawnService(
      resolvePython(),
      ["-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8000"],
      projectRoot,
      "backend"
    );

    await waitForServer(
      async () => {
        const response = await requestJson("http://127.0.0.1:8000/health");
        return response.statusCode === 200 && response.body.status === "healthy";
      },
      45000,
      "Backend"
    );
    backendReady = true;

    updateSplash("Starting frontend", "Launching the local workbench...");
    if (app.isPackaged) {
      await startStaticFrontendServer(frontendDir);
    } else {
      frontendProcess = spawnService(
        npmCommand,
        ["run", fs.existsSync(path.join(frontendDir, ".next", "BUILD_ID")) ? "start" : "dev"],
        frontendDir,
        "frontend"
      );
    }

    await waitForServer(
      async () => {
        const statusCode = await requestStatus("http://127.0.0.1:3000");
        return statusCode === 200;
      },
      60000,
      "Frontend"
    );
    frontendReady = true;

    updateSplash("Opening workbench", "Desktop services are online.");
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.loadURL("http://127.0.0.1:3000");
    }
  } catch (error) {
    showFailure("Startup", error.message);
  }
}

app.whenReady().then(() => {
  installElectronNetworkGuard();
  ensureLogDir();
  createWindow();
  bootstrapDesktop();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
      if (frontendReady) {
        mainWindow.loadURL("http://127.0.0.1:3000");
      }
    }
  });
});

app.on("before-quit", () => {
  stopStaticFrontend();
  stopService(frontendProcess);
  stopService(backendProcess);
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

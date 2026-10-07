const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const http = require("http");

const URL = "http://127.0.0.1:8787";

function waitForServer(retries = 60) {
  return new Promise((resolve, reject) => {
    const check = () => {
      const req = http.get(URL + "/health", res => {
        res.resume();
        if (res.statusCode >= 200 && res.statusCode < 500) return resolve();
        retry();
      });
      req.on("error", retry);
      req.setTimeout(1000, () => { req.destroy(); retry(); });
    };
    let n = 0;
    const retry = () => {
      if (++n >= retries) return reject(new Error("JARVIS server did not start on 127.0.0.1:8787"));
      setTimeout(check, 500);
    };
    check();
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1500,
    height: 900,
    minWidth: 1000,
    minHeight: 650,
    title: "DARSHAN JARVIS 2.0",
    backgroundColor: "#020202",
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  win.once("ready-to-show", () => win.show());
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
  win.loadURL(URL);
}

app.whenReady().then(async () => {
  try {
    await waitForServer();
    createWindow();
  } catch (err) {
    const { dialog } = require("electron");
    dialog.showErrorBox("JARVIS", err.message);
    app.quit();
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

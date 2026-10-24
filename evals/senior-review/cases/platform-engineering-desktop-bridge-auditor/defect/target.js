// Electron bridge source packet. Requirement: renderer save writes text through the only main handler. ipcMain/ipcRenderer are supplied host APIs.
export function register(ipcMain, write) { ipcMain.handle("save-file", (_event, text) => write(text)); }
export function expose(ipcRenderer) { return {save: text => ipcRenderer.invoke("save-document", text)}; }

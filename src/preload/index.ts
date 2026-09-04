import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom APIs for renderer
const api = {
  getBackendConfig: (): Promise<{ apiUrl: string; wsUrl: string }> =>
    ipcRenderer.invoke('get-backend-config'),
  checkBackendHealth: (): Promise<boolean> =>
    ipcRenderer.invoke('check-backend-health'),
  minimizeWindow: (): Promise<void> =>
    ipcRenderer.invoke('window-minimize'),
  maximizeWindow: (): Promise<void> =>
    ipcRenderer.invoke('window-maximize'),
  closeWindow: (): Promise<void> =>
    ipcRenderer.invoke('window-close'),
  openPath: (targetPath: string): Promise<boolean> =>
    ipcRenderer.invoke('open-path', targetPath),
  getPlatform: (): Promise<string> =>
    ipcRenderer.invoke('get-platform'),
  getBackendStatus: (): Promise<any> =>
    ipcRenderer.invoke('get-backend-status'),
  openBackendLog: (): Promise<boolean> =>
    ipcRenderer.invoke('open-backend-log'),
  restartBackend: (): Promise<boolean> =>
    ipcRenderer.invoke('restart-backend')
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}

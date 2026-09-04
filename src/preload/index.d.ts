import { ElectronAPI } from '@electron-toolkit/preload'

interface CustomAPI {
  getBackendConfig: () => Promise<{ apiUrl: string; wsUrl: string }>
  checkBackendHealth: () => Promise<boolean>
  minimizeWindow: () => Promise<void>
  maximizeWindow: () => Promise<void>
  closeWindow: () => Promise<void>
  openPath: (targetPath: string) => Promise<boolean>
  getPlatform: () => Promise<string>
  getBackendStatus: () => Promise<any>
  openBackendLog: () => Promise<boolean>
  restartBackend: () => Promise<boolean>
}

declare global {
  interface Window {
    electron: ElectronAPI
    api: CustomAPI
  }
}

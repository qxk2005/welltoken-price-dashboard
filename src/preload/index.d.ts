import { ElectronAPI } from '@electron-toolkit/preload'

interface CustomAPI {
  getBackendConfig: () => Promise<{ apiUrl: string; wsUrl: string }>
  checkBackendHealth: () => Promise<boolean>
  minimizeWindow: () => Promise<void>
  maximizeWindow: () => Promise<void>
  closeWindow: () => Promise<void>
}

declare global {
  interface Window {
    electron: ElectronAPI
    api: CustomAPI
  }
}

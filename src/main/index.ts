import { app, shell, BrowserWindow, ipcMain, session } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { pyManager } from './pyManager'

// 关键加固 1: 早期强制 Chromium 将本地回环地址加入代理绕过名单，防止系统代理劫持本地端口
app.commandLine.appendSwitch('proxy-bypass-list', '<local>;127.0.0.1;localhost;::1')

let mainWindow: BrowserWindow | null = null

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1024,
    minHeight: 680,
    show: false,
    autoHideMenuBar: true,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    trafficLightPosition: process.platform === 'darwin' ? { x: 14, y: 14 } : undefined,
    backgroundColor: '#0B0E14',
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote url for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// 注册 IPC 处理程序
function setupIpc(): void {
  ipcMain.handle('get-backend-config', () => {
    return {
      apiUrl: pyManager.getApiUrl(),
      wsUrl: pyManager.getWsUrl()
    }
  })

  ipcMain.handle('get-backend-status', () => {
    return pyManager.getStatus()
  })

  ipcMain.handle('open-backend-log', async () => {
    try {
      const logPath = pyManager.getLogFilePath()
      if (logPath) {
        await shell.openPath(logPath)
        return true
      }
      return false
    } catch (e) {
      console.error('Failed to open backend log:', e)
      return false
    }
  })

  ipcMain.handle('restart-backend', async () => {
    try {
      pyManager.stop()
      await new Promise((r) => setTimeout(r, 1000))
      await pyManager.start()
      return await pyManager.isBackendHealthy()
    } catch (e) {
      console.error('Failed to restart backend:', e)
      return false
    }
  })

  ipcMain.handle('check-backend-health', async () => {
    return await pyManager.isBackendHealthy()
  })

  ipcMain.handle('window-minimize', () => {
    mainWindow?.minimize()
  })

  ipcMain.handle('window-maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize()
    } else {
      mainWindow?.maximize()
    }
  })

  ipcMain.handle('window-close', () => {
    mainWindow?.close()
  })

  ipcMain.handle('open-path', async (_, targetPath: string) => {
    try {
      if (targetPath) {
        await shell.openPath(targetPath)
        return true
      }
      return false
    } catch (e) {
      console.error('Failed to open path:', e)
      return false
    }
  })

  ipcMain.handle('get-platform', () => {
    return process.platform
  })
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
app.whenReady().then(async () => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.welltoken.pricedashboard')

  // 关键加固 2: 确保当前 Session 强制将本地回环排除在代理外
  try {
    await session.defaultSession.setProxy({
      mode: 'system',
      proxyBypassRules: '<local>;127.0.0.1;localhost;::1'
    })
  } catch (err) {
    console.warn('[ProxyBypass] Warning configuring session proxy bypass:', err)
  }

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  setupIpc()

  // 启动后台 Python 进程
  try {
    await pyManager.start()
  } catch (err) {
    console.error('Failed to start python backend:', err)
  }

  createWindow()

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 在应用退出前优雅终止 Python 子进程
app.on('before-quit', () => {
  pyManager.stop()
})

app.on('will-quit', () => {
  pyManager.stop()
})

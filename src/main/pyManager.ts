import { spawn, ChildProcess, execSync } from 'child_process'
import { app } from 'electron'
import { join } from 'path'
import http from 'http'
import fs from 'fs'
import os from 'os'

export class PythonProcessManager {
  private pyProcess: ChildProcess | null = null
  private port: number = 8765
  private host: string = '127.0.0.1'
  private lastError: string | null = null
  private logFilePath: string = ''

  constructor(port = 8765, host = '127.0.0.1') {
    this.port = port
    this.host = host
    this.initLogPath()
  }

  private initLogPath(): void {
    const home = os.homedir()
    let logDir: string
    if (process.platform === 'darwin') {
      logDir = join(home, 'Library', 'Application Support', 'WellTokenDashboard', 'logs')
    } else if (process.platform === 'win32') {
      logDir = join(process.env.APPDATA || home, 'WellTokenDashboard', 'logs')
    } else {
      logDir = join(home, '.welltoken_dashboard', 'logs')
    }
    try {
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true })
      }
      this.logFilePath = join(logDir, 'backend.log')
    } catch (e) {
      console.warn('[PythonManager] Failed to init log directory:', e)
      this.logFilePath = join(os.tmpdir(), 'welltoken_backend.log')
    }
  }

  public getLogFilePath(): string {
    return this.logFilePath
  }

  public log(message: string, isError = false): void {
    const timestamp = new Date().toISOString()
    const formatted = `[${timestamp}] ${message}\n`
    if (isError) {
      console.error(formatted.trim())
    } else {
      console.log(formatted.trim())
    }
    try {
      if (this.logFilePath) {
        fs.appendFileSync(this.logFilePath, formatted, 'utf-8')
      }
    } catch {
      // 忽略日志文件写入异常
    }
  }

  public getApiUrl(): string {
    return `http://${this.host}:${this.port}`
  }

  public getWsUrl(): string {
    return `ws://${this.host}:${this.port}/api/v1/price/ws`
  }

  public getLastError(): string | null {
    return this.lastError
  }

  public getStatus() {
    return {
      isRunning: !!this.pyProcess,
      lastError: this.lastError,
      logFilePath: this.logFilePath,
      port: this.port,
      host: this.host,
      apiUrl: this.getApiUrl(),
      wsUrl: this.getWsUrl()
    }
  }

  public async isBackendHealthy(): Promise<boolean> {
    return new Promise((resolve) => {
      const req = http.get(`${this.getApiUrl()}/api/v1/system/health`, (res) => {
        resolve(res.statusCode === 200)
      })
      req.on('error', () => resolve(false))
      req.setTimeout(1000, () => {
        req.destroy()
        resolve(false)
      })
    })
  }

  private resolvePythonExecutable(): string {
    const home = os.homedir()
    const candidates = [
      // 1. 用户 pyenv WPD 虚拟环境
      join(home, '.pyenv/versions/WPD/bin/python'),
      join(home, '.pyenv/versions/WPD/bin/python3'),
      // 2. 当前激活虚拟环境
      process.env.VIRTUAL_ENV ? join(process.env.VIRTUAL_ENV, 'bin/python') : '',
      // 3. 全局 python3 / python
      'python3',
      'python'
    ]

    for (const candidate of candidates) {
      if (candidate && (candidate === 'python3' || candidate === 'python' || fs.existsSync(candidate))) {
        return candidate
      }
    }
    return 'python3'
  }

  public async start(): Promise<void> {
    this.log(`[PythonManager] Starting backend service on ${this.host}:${this.port}...`)

    // 首先检查是否已有本地服务在运行（避免重复启动）
    const alreadyRunning = await this.isBackendHealthy()
    if (alreadyRunning) {
      this.log(`[PythonManager] Backend is already running and healthy on port ${this.port}.`)
      return
    }

    const isPackaged = app.isPackaged
    const spawnEnv: NodeJS.ProcessEnv = {
      ...process.env,
      NO_PROXY: '127.0.0.1,localhost,::1',
      no_proxy: '127.0.0.1,localhost,::1',
      PYTHONUNBUFFERED: '1'
    }

    if (isPackaged) {
      // 生产环境：调用 extraResources 中的二进制
      const isWin = process.platform === 'win32'
      const isMac = process.platform === 'darwin'
      const binaryName = isWin ? 'backend-server.exe' : 'backend-server'
      const binaryPath = join(process.resourcesPath, 'bin', binaryName)

      // macOS 专属权限加固与 Gatekeeper Quarantine 隔离属性脱敏
      if (isMac) {
        try {
          const binDir = join(process.resourcesPath, 'bin')
          if (fs.existsSync(binDir)) {
            try {
              execSync(`xattr -d -r com.apple.quarantine "${binDir}" 2>/dev/null || xattr -c -r "${binDir}" 2>/dev/null || true`, { stdio: 'ignore' })
            } catch {
              // ignore
            }
          }
          if (fs.existsSync(binaryPath)) {
            fs.chmodSync(binaryPath, 0o755)
            try {
              execSync(`xattr -d com.apple.quarantine "${binaryPath}" 2>/dev/null || xattr -c "${binaryPath}" 2>/dev/null || true`, { stdio: 'ignore' })
            } catch {
              // ignore
            }
          }
          this.log(`[PythonManager] macOS quarantine stripped and chmod 755 applied for: ${binaryPath}`)
        } catch (e) {
          this.log(`[PythonManager] Notice while stripping quarantine / chmod: ${e}`)
        }
      } else if (!isWin && fs.existsSync(binaryPath)) {
        try {
          fs.chmodSync(binaryPath, 0o755)
        } catch (e) {
          this.log(`[PythonManager] Failed to chmod binary: ${e}`, true)
        }
      }

      if (!fs.existsSync(binaryPath)) {
        const errMsg = `Bundled backend binary not found at: ${binaryPath}`
        this.lastError = errMsg
        this.log(`[PythonManager] Error: ${errMsg}`, true)
        return
      }

      const home = os.homedir()
      let workDir = join(home, 'Library', 'Application Support', 'WellTokenDashboard')
      if (process.platform === 'win32') {
        workDir = join(process.env.APPDATA || home, 'WellTokenDashboard')
      } else if (process.platform !== 'darwin') {
        workDir = join(home, '.welltoken_dashboard')
      }
      try {
        if (!fs.existsSync(workDir)) {
          fs.mkdirSync(workDir, { recursive: true })
        }
      } catch {
        workDir = os.tmpdir()
      }

      this.log(`[PythonManager] Spawning bundled Python binary: ${binaryPath} (cwd: ${workDir})`)
      try {
        this.pyProcess = spawn(binaryPath, ['--host', this.host, '--port', this.port.toString()], {
          cwd: workDir,
          detached: false,
          env: spawnEnv,
          stdio: 'pipe'
        })
      } catch (err: any) {
        this.lastError = `Failed to spawn backend process: ${err?.message || err}`
        this.log(`[PythonManager] Spawn exception: ${this.lastError}`, true)
        return
      }
    } else {
      // 开发环境：定位 pyenv WPD 环境调用 python backend/run_server.py
      const projectRoot = join(__dirname, '../../')
      const scriptPath = join(projectRoot, 'backend', 'run_server.py')
      const pythonExe = this.resolvePythonExecutable()

      this.log(`[PythonManager] Launching dev Python backend: ${pythonExe} -> ${scriptPath}`)
      try {
        this.pyProcess = spawn(pythonExe, [scriptPath, '--host', this.host, '--port', this.port.toString()], {
          cwd: projectRoot,
          detached: false,
          env: {
            ...spawnEnv,
            PYTHONPATH: projectRoot
          },
          stdio: 'pipe'
        })
      } catch (err: any) {
        this.lastError = `Failed to spawn dev python backend: ${err?.message || err}`
        this.log(`[PythonManager] Dev spawn exception: ${this.lastError}`, true)
        return
      }
    }

    this.pyProcess?.stdout?.on('data', (data) => {
      const text = data.toString().trim()
      if (text) {
        this.log(`[STDOUT] ${text}`)
      }
    })

    this.pyProcess?.stderr?.on('data', (data) => {
      const text = data.toString().trim()
      if (text) {
        this.log(`[STDERR] ${text}`, true)
      }
    })

    this.pyProcess?.on('error', (err) => {
      this.lastError = `Process runtime error: ${err.message}`
      this.log(`[PythonManager] Process error event: ${err.stack || err.message}`, true)
    })

    this.pyProcess?.on('close', (code, signal) => {
      this.log(`[PythonManager] Backend process exited with code=${code}, signal=${signal}`)
      if (code !== 0 && code !== null) {
        this.lastError = `Backend exited abnormally with code ${code} (signal: ${signal || 'none'})`
      }
      this.pyProcess = null
    })

    // 等待服务就绪（最多等待 25 秒）
    let attempts = 0
    while (attempts < 50) {
      await new Promise((r) => setTimeout(r, 500))
      if (await this.isBackendHealthy()) {
        this.log(`[PythonManager] Backend successfully started and healthy at ${this.getApiUrl()}!`)
        this.lastError = null
        return
      }
      attempts++
    }
    const timeoutMsg = `Backend readiness check timed out after 25s. Last error: ${this.lastError || 'None reported'}`
    this.log(`[PythonManager] Warning: ${timeoutMsg}`, true)
    if (!this.lastError) {
      this.lastError = timeoutMsg
    }
  }

  public stop(): void {
    if (this.pyProcess) {
      this.log(`[PythonManager] Terminating Python backend process...`)
      try {
        this.pyProcess.kill('SIGTERM')
      } catch (e) {
        this.log(`[PythonManager] Failed to kill process: ${e}`, true)
      }
      this.pyProcess = null
    }
  }
}

export const pyManager = new PythonProcessManager()

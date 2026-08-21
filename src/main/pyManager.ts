import { spawn, ChildProcess } from 'child_process'
import { app } from 'electron'
import { join } from 'path'
import http from 'http'
import fs from 'fs'
import os from 'os'

export class PythonProcessManager {
  private pyProcess: ChildProcess | null = null
  private port: number = 8765
  private host: string = '127.0.0.1'

  constructor(port = 8765, host = '127.0.0.1') {
    this.port = port
    this.host = host
  }

  public getApiUrl(): string {
    return `http://${this.host}:${this.port}`
  }

  public getWsUrl(): string {
    return `ws://${this.host}:${this.port}/api/v1/price/ws`
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
    // 首先检查是否已有本地服务在运行（避免重复启动）
    const alreadyRunning = await this.isBackendHealthy()
    if (alreadyRunning) {
      console.log(`[PythonManager] Backend is already running on port ${this.port}.`)
      return
    }

    const isPackaged = app.isPackaged

    if (isPackaged) {
      // 生产环境：调用 extraResources 中的二进制
      const isWin = process.platform === 'win32'
      const binaryName = isWin ? 'backend-server.exe' : 'backend-server'
      const binaryPath = join(process.resourcesPath, 'bin', binaryName)

      console.log(`[PythonManager] Launching bundled Python binary from: ${binaryPath}`)
      this.pyProcess = spawn(binaryPath, ['--host', this.host, '--port', this.port.toString()], {
        detached: false,
        stdio: 'pipe'
      })
    } else {
      // 开发环境：定位 pyenv WPD 环境调用 python backend/run_server.py
      const projectRoot = join(__dirname, '../../')
      const scriptPath = join(projectRoot, 'backend', 'run_server.py')
      const pythonExe = this.resolvePythonExecutable()

      console.log(`[PythonManager] Launching Python backend with: ${pythonExe} -> ${scriptPath}`)
      this.pyProcess = spawn(pythonExe, [scriptPath, '--host', this.host, '--port', this.port.toString()], {
        cwd: projectRoot,
        detached: false,
        env: {
          ...process.env,
          PYTHONPATH: projectRoot
        },
        stdio: 'pipe'
      })
    }

    this.pyProcess?.stdout?.on('data', (data) => {
      console.log(`[Python Backend STDOUT]: ${data.toString().trim()}`)
    })

    this.pyProcess?.stderr?.on('data', (data) => {
      console.error(`[Python Backend STDERR]: ${data.toString().trim()}`)
    })

    this.pyProcess?.on('close', (code) => {
      console.log(`[PythonManager] Backend process exited with code ${code}`)
      this.pyProcess = null
    })

    // 等待服务就绪（最多等待 15 秒）
    let attempts = 0
    while (attempts < 30) {
      await new Promise((r) => setTimeout(r, 500))
      if (await this.isBackendHealthy()) {
        console.log(`[PythonManager] Backend successfully started and healthy!`)
        return
      }
      attempts++
    }
    console.warn(`[PythonManager] Backend readiness check timed out.`)
  }

  public stop(): void {
    if (this.pyProcess) {
      console.log(`[PythonManager] Terminating Python backend process...`)
      try {
        this.pyProcess.kill('SIGTERM')
      } catch (e) {
        console.error(`[PythonManager] Failed to kill process:`, e)
      }
      this.pyProcess = null
    }
  }
}

export const pyManager = new PythonProcessManager()

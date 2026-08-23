import { execFile } from 'child_process';
import { promisify } from 'util';
import fs from 'fs';
import path from 'path';

const execFileAsync = promisify(execFile);

/**
 * 自动探测系统中可用的 Chrome / Edge 浏览器可执行文件路径
 */
function findBrowserExecutable() {
  const possiblePaths = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    path.join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe'),
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'
  ];

  for (const p of possiblePaths) {
    if (fs.existsSync(p)) {
      return p;
    }
  }
  return null;
}

/**
 * 执行 Headless 截图与页面渲染验证
 * @param {Object} options
 * @param {string} options.url 目标测试网址 (默认: http://localhost:5173/)
 * @param {string} options.outputPath 截图输出绝对路径
 * @param {number} options.width 视口宽度 (默认: 1440)
 * @param {number} options.height 视口高度 (默认: 900)
 * @param {number} options.delay 虚拟等待时间 (毫秒, 默认: 3000)
 */
export async function captureScreenshot(options = {}) {
  const url = options.url || 'http://localhost:5173/';
  const width = options.width || 1440;
  const height = options.height || 900;
  const delay = options.delay || 3000;
  
  const defaultOutputDir = path.resolve('design/screenshots');
  if (!fs.existsSync(defaultOutputDir)) {
    fs.mkdirSync(defaultOutputDir, { recursive: true });
  }

  const outputPath = options.outputPath || path.join(defaultOutputDir, `screenshot_${Date.now()}.png`);
  const browserPath = findBrowserExecutable();

  if (!browserPath) {
    throw new Error('未找到可用的 Chrome 或 Edge 浏览器执行程序。');
  }

  const args = [
    '--headless=new',
    `--screenshot=${outputPath}`,
    `--window-size=${width},${height}`,
    `--virtual-time-budget=${delay}`,
    '--hide-scrollbars',
    '--disable-gpu',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    url
  ];

  console.log(`[Headless Tester] 正在启动渲染引擎: ${browserPath}`);
  console.log(`[Headless Tester] 正在截取: ${url} (分辨率: ${width}x${height})`);

  await execFileAsync(browserPath, args);

  if (fs.existsSync(outputPath)) {
    const stats = fs.statSync(outputPath);
    console.log(`[Headless Tester] ✅ 截图成功保存至: ${outputPath} (${(stats.size / 1024).toFixed(1)} KB)`);
    return {
      success: true,
      outputPath,
      fileSizeBytes: stats.size,
      width,
      height,
      url,
      timestamp: new Date().toISOString()
    };
  } else {
    throw new Error(`截图文件未生成: ${outputPath}`);
  }
}

// 允许直接通过命令行执行: node scripts/screenshot_tester.mjs [url] [outputPath]
if (import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const targetUrl = process.argv[2] || 'http://localhost:5173/';
  const targetOutput = process.argv[3];

  captureScreenshot({ url: targetUrl, outputPath: targetOutput })
    .then(res => {
      console.log(JSON.stringify(res, null, 2));
      process.exit(0);
    })
    .catch(err => {
      console.error('[Headless Tester] ❌ 截图失败:', err.message);
      process.exit(1);
    });
}

import { resolve } from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 专用于纯 Web 浏览器模式调试的 Vite 配置 (npm run dev:browser / npm run dev:web)
export default defineConfig({
  root: resolve(__dirname, 'src/renderer'),
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src/renderer/src')
    }
  },
  server: {
    port: 5173,
    host: '0.0.0.0', // 监听全部网络接口 (同时兼容 localhost, 127.0.0.1 与局域网 IP)
    strictPort: true,
    cors: true
  }
})

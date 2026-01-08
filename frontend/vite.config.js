import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'  // <--- 修改点：这里必须有 @ 符号

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',  // 允许局域网访问
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 后端地址
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})

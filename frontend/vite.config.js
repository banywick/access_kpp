// frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://backend:8000',  // Используем имя сервиса backend из docker-compose
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err)
          })
        }
      },
      '/media': {
        target: 'http://backend:8000',  // Используем имя сервиса backend
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
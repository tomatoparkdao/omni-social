import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig(({ command }) => {
  // 生产构建必须使用生产认证模式；local_dev 只允许本机开发使用。
  const authMode = (process.env.OMNISOCIAL_AUTH_MODE || 'production').trim().toLowerCase()
  if (command === 'build' && authMode !== 'production') {
    throw new Error(`生产构建拒绝 OMNISOCIAL_AUTH_MODE=${authMode}：请使用 production 构建并部署。`)
  }

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          // 移除自动导入，改用@use语法
        }
      }
    },
    server: {
      port: 5173,
      open: true,
      proxy: {
        // 固定使用回环 IPv4：后端只监听 127.0.0.1，避免 localhost 解析到 ::1 导致代理失败。
        '/api': {
          target: 'http://127.0.0.1:5409',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      chunkSizeWarningLimit: 1600,
      rollupOptions: {
        output: {
          manualChunks: {
            vue: ['vue', 'vue-router', 'pinia'],
            elementPlus: ['element-plus'],
            utils: ['axios']
          }
        }
      }
    }
  }
})

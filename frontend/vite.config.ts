import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('/node_modules/vue/') || id.includes('/node_modules/vue-router/')) return 'vue'
          if (id.includes('@element-plus/icons-vue')) return 'element-icons'
          if (id.includes('element-plus')) return 'element-ui'
          if (id.includes('echarts')) return 'charts'
          if (id.includes('animejs')) return 'motion'
          return 'vendor'
        },
      },
    },
  },
  server: {
    port: 5174,
    host: '0.0.0.0',
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: 'C:/Users/33253/Documents/New project/astrbot_plugin_sra_rms/webui-backend/wwwroot',
    emptyOutDir: false
  },
  server: {
    host: '127.0.0.1',
    port: 5173
  }
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // In production the React build is served by FastAPI at /site/.
  // Setting base ensures all JS/CSS asset paths resolve correctly.
  base: command === 'build' ? '/site/' : '/',
  css: {
    postcss: {
      plugins: [tailwindcss(), autoprefixer()],
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/predict': 'http://127.0.0.1:5000',
      '/sample-images': 'http://127.0.0.1:5000',
      '/policy': 'http://127.0.0.1:5000',
      '/reports': 'http://127.0.0.1:5000',
      '/scan': 'http://127.0.0.1:8000',
      '/dashboard': 'http://127.0.0.1:8000',
      '/dashboard/summary': 'http://127.0.0.1:8000',
      '/dashboard/scans': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/yolo': 'http://127.0.0.1:8000',
    },
    watch: {
      // Ignore WinRAR temp files that crash the fs watcher
      ignored: ['**/*.rartemp', '**/__rzi_*', '**/node.zip'],
    },
  },
}))

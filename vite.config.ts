import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      // Ignore WinRAR temp files that crash the fs watcher
      ignored: ['**/*.rartemp', '**/__rzi_*', '**/node.zip'],
    },
  },
})

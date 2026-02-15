import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const isDev = mode === 'development'
  
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/users': 'http://localhost:8000',
        '/tasks': 'http://localhost:8000',
        '/energy': 'http://localhost:8000',
        '/api': 'http://localhost:8000'
      }
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: !isDev,
          drop_debugger: !isDev
        }
      },
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom']
          }
        }
      },
      sourcemap: isDev,
      chunkSizeWarningLimit: 500
    },
    preview: {
      port: 4173
    }
  }
})

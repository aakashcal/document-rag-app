import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'


// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Enable build optimizations
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        // Chunk vendor files
        manualChunks: {
          vendor: ['react', 'react-dom', '@tanstack/react-query'],
          ui: ['react/jsx-runtime']
        }
      }
    },
    // Generate sourcemaps for easier debugging
    sourcemap: true,
  },
  server: {
    // Configure proxy for API requests
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  // Improve HMR performance
  optimizeDeps: {
    include: ['react', 'react-dom', '@tanstack/react-query']
  }
})

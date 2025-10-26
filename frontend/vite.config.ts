import { defineConfig } from 'vite'
import fs from 'fs';
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['react/compiler-runtime'],
  },
  server: {
    https: {
      key: fs.readFileSync('../localhost-key.pem'),
      cert: fs.readFileSync('../localhost.pem'),
    },
    host: 'localhost',
    port: 5173, // or your preferred port
    proxy: {
      '/api': {
        target: 'https:127.0.0.1:8000', // Updated to public ngrok URL
        changeOrigin: true,
      },
    },
  },
})

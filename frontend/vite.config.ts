import { defineConfig } from 'vite'
// import fs from 'fs'; // Removed, not used
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['react/compiler-runtime'],
  },
  
  // host and port removed for deployment
  server: {
    proxy: {
      '/api': {
        target: 'https://shopify-app1-0.onrender.com', // Updated to deployed backend URL
        changeOrigin: true,
      },
    },
  },
})

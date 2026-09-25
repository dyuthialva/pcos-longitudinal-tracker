import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    headers: {
      // Security: only allow resources from trusted sources.
      // connect-src currently allows localhost for development;
      // add the FastAPI origin here when the backend is connected.
      'Content-Security-Policy':
        "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self'; font-src 'self' data:; connect-src 'self' http://localhost:*;",
      
      // Security: limit information sent to other sites through the Referer header.
      'Referrer-Policy': 'strict-origin-when-cross-origin',
    },
  },
})
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Standard Vite + React config. dev server runs on localhost:5173 by default.
export default defineConfig({
  plugins: [react()],
})

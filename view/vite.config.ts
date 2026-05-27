import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  root: 'app',
  base: '/static/',
  plugins: [react()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/audio': 'http://127.0.0.1:8000',
      '/visuals': 'http://127.0.0.1:8000',
    },
  },
});

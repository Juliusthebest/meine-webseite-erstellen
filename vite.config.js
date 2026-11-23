import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base: './' erlaubt das Hosten in Unterordnern (z. B. GitHub Pages)
export default defineConfig({
  base: './',
  plugins: [react()],
});

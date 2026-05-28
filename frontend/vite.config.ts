import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react(),
  ],
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    target: 'esnext',
    cssCodeSplit: false,
    outDir: 'dist',
    emptyOutDir: true,
    lib: {
      entry: './src/main.tsx',
      name: 'WalletMonitorPlugin',
      fileName: 'index',
      formats: ['es'],
    },
    rollupOptions: {
      // 将 react 和 react-dom 作为外部依赖
      // 插件运行时复用 QuantCell 主应用暴露的 window.React / window.ReactDOM
      external: ['react', 'react-dom', 'react-dom/client', 'react/jsx-runtime'],
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
          'react-dom/client': 'ReactDOM',
          'react/jsx-runtime': 'ReactJSX',
        },
      },
    },
  },
});

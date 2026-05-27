import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import type { Plugin } from 'vite';

// 匹配 JS 标识符（包括 $ 和 Unicode 字符，与 Rollup 压缩后的变量名兼容）
const IDENT = String.raw`[\p{ID_Start}$_][\p{ID_Continue}$\u200C\u200D]*`;

function externalsToGlobals(): Plugin {
  const moduleMap: Record<string, string> = {
    'react': 'React',
    'react-dom': 'ReactDOM',
    'react-dom/client': 'ReactDOM',
    'react/jsx-runtime': 'ReactJSX',
  };

  function transformImports(code: string): string {
    let result = code;
    for (const [mod, globalName] of Object.entries(moduleMap)) {
      const escaped = mod.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

      // 1) import * as X from "mod"
      const nsRe = new RegExp(
        `import\\s+\\*\\s+as\\s+(${IDENT})\\s+from\\s*"${escaped}"\\s*;?`,
        'gu'
      );
      result = result.replace(nsRe, (_m: string, name: string) =>
        `const ${name} = ${globalName};`
      );

      // 2) import X, { a, b as c } from "mod"
      const defNamedRe = new RegExp(
        `import\\s+(${IDENT})\\s*,\\s*\\{([^}]+)\\}\\s+from\\s*"${escaped}"\\s*;?`,
        'gu'
      );
      result = result.replace(defNamedRe, (_m: string, defName: string, named: string) => {
        const parts = [`const ${defName} = ${globalName};`];
        parseNamedImports(named, globalName, parts);
        return parts.join('\n');
      });

      // 3) import { a, b as c } from "mod"
      const namedRe = new RegExp(
        `import\\s+\\{([^}]+)\\}\\s+from\\s*"${escaped}"\\s*;?`,
        'gu'
      );
      result = result.replace(namedRe, (_m: string, named: string) => {
        const parts: string[] = [];
        parseNamedImports(named, globalName, parts);
        return parts.join('\n');
      });

      // 4) import X from "mod"
      const defRe = new RegExp(
        `import\\s+(${IDENT})\\s+from\\s*"${escaped}"\\s*;?`,
        'gu'
      );
      result = result.replace(defRe, (_m: string, name: string) =>
        `const ${name} = ${globalName};`
      );
    }
    return result;
  }

  function parseNamedImports(named: string, globalName: string, parts: string[]): void {
    for (const item of named.split(',')) {
      const t = item.trim();
      if (!t) continue;
      // 使用宽松的正则匹配标识符，支持 $ 符号（Rollup 压缩后的变量名如 $t）
      const asMatch = t.match(new RegExp(`^(${IDENT})\\s+as\\s+(${IDENT})$`, 'u'));
      if (asMatch) {
        parts.push(`const ${asMatch[2]} = ${globalName}.${asMatch[1]};`);
      } else {
        parts.push(`const ${t} = ${globalName}.${t};`);
      }
    }
  }

  return {
    name: 'externals-to-globals',
    generateBundle(_options, bundle) {
      for (const chunk of Object.values(bundle)) {
        if (chunk.type === 'chunk') {
          chunk.code = transformImports(chunk.code);
        }
      }
    },
  };
}

export default defineConfig({
  plugins: [
    react(),
    externalsToGlobals(),
  ],
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    target: 'esnext',
    lib: {
      entry: 'src/main.tsx',
      formats: ['es'],
      fileName: 'index',
    },
    rollupOptions: {
      external: ['react', 'react-dom', 'react/jsx-runtime', 'react-dom/client'],
      output: {
        entryFileNames: 'index.js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
    cssCodeSplit: false,
    outDir: 'dist',
    emptyOutDir: true,
  },
});

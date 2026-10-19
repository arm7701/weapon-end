import path from 'node:path'
import { createReadStream, existsSync, statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteStaticCopy } from 'vite-plugin-static-copy'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const cesiumSource = path.resolve(__dirname, 'node_modules/cesium/Build/Cesium')
const cesiumBaseUrl = 'cesium-static'
const configuredBase = process.env.VITE_BASE_PATH || '/'
const publicBase = configuredBase.endsWith('/') ? configuredBase : `${configuredBase}/`
const apiProxyTarget = process.env.VITE_API_PROXY || 'http://127.0.0.1:8000'

function mimeType(filePath) {
  if (filePath.endsWith('.js')) return 'application/javascript'
  if (filePath.endsWith('.css')) return 'text/css'
  if (filePath.endsWith('.json')) return 'application/json'
  if (filePath.endsWith('.wasm')) return 'application/wasm'
  if (filePath.endsWith('.png')) return 'image/png'
  if (filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) return 'image/jpeg'
  if (filePath.endsWith('.gif')) return 'image/gif'
  if (filePath.endsWith('.svg')) return 'image/svg+xml'
  if (filePath.endsWith('.webp')) return 'image/webp'
  if (filePath.endsWith('.woff2')) return 'font/woff2'
  return 'application/octet-stream'
}

/** Serve full Cesium Build folder in Vite dev (including Cesium.js). */
function serveCesiumStatic() {
  return {
    name: 'serve-cesium-static',
    configureServer(server) {
      server.middlewares.use(`/${cesiumBaseUrl}`, (req, res, next) => {
        try {
          const rel = decodeURIComponent((req.url || '/').split('?')[0]).replace(/^\/+/, '')
          const file = path.resolve(cesiumSource, rel)
          if (!file.startsWith(cesiumSource) || !existsSync(file) || !statSync(file).isFile()) {
            next()
            return
          }
          res.setHeader('Content-Type', mimeType(file))
          res.setHeader('Cache-Control', 'public, max-age=86400')
          createReadStream(file).pipe(res)
        } catch {
          next()
        }
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  base: publicBase,
  define: {
    CESIUM_BASE_URL: JSON.stringify(`${publicBase}${cesiumBaseUrl}`),
  },
  server: {
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
    fs: {
      allow: [__dirname, cesiumSource],
    },
  },
  optimizeDeps: {
    include: ['xlsx'],
  },
  build: {
    chunkSizeWarningLimit: 4000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('node_modules/cesium')) return 'cesium'
          if (id.includes('node_modules/@cesium')) return 'cesium'
          if (id.includes('node_modules/jspdf')) return 'export-pdf'
          if (id.includes('node_modules/html2canvas')) return 'export-pdf'
          if (id.includes('node_modules/dompurify')) return 'export-pdf'
          if (id.includes('node_modules/docx')) return 'export-word'
          if (id.includes('node_modules/@zip.js')) return 'export-word'
          if (id.includes('node_modules/xlsx')) return 'export-excel'
          return 'vendor'
        },
      },
    },
  },
  plugins: [
    vue(),
    serveCesiumStatic(),
    viteStaticCopy({
      targets: [
        { src: `${cesiumSource.replace(/\\/g, '/')}/Cesium.js`, dest: cesiumBaseUrl },
        { src: `${cesiumSource.replace(/\\/g, '/')}/Workers`, dest: cesiumBaseUrl },
        { src: `${cesiumSource.replace(/\\/g, '/')}/ThirdParty`, dest: cesiumBaseUrl },
        { src: `${cesiumSource.replace(/\\/g, '/')}/Assets`, dest: cesiumBaseUrl },
        { src: `${cesiumSource.replace(/\\/g, '/')}/Widgets`, dest: cesiumBaseUrl },
      ],
    }),
  ],
})

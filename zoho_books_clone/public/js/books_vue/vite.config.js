import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

// Vue + Vue Router are bundled (not externalised). The legacy SPA loaded them
// from a CDN; the new bundle is self-contained so the app works on networks
// that block unpkg.
export default defineConfig({
  plugins: [vue()],
  build: {
    outDir:      resolve(__dirname, "../../js"),
    assetsDir:   "dist",
    emptyOutDir: false,
    lib: {
      entry:    resolve(__dirname, "src/main.js"),
      name:     "BooksApp",
      fileName: () => "books.js",
      formats:  ["iife"],
    },
    rollupOptions: {
      output: {
        assetFileNames: "dist/[name][extname]",
      },
    },
    minify:       true,
    cssCodeSplit: false,
  },
  resolve: {
    alias: { "@": resolve(__dirname, "src") },
  },
});

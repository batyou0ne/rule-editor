import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { quasar, transformAssetUrls } from "@quasar/vite-plugin";
import { fileURLToPath, URL } from "node:url";

const eflintApiBaseUrl = process.env.VITE_EFLINT_API_BASE_URL || "http://localhost:8000";
const eflintExecuteBaseUrl = process.env.VITE_EFLINT_EXECUTE_URL || "http://localhost:8001";
const eflintServerBaseUrl = process.env.VITE_EFLINT_SERVER_BASE_URL || "http://localhost:8080";
const authApiBaseUrl = process.env.VITE_AUTH_API_BASE_URL || "http://localhost:8101";
const mongoApiBaseUrl = process.env.VITE_MONGO_API_BASE_URL || "http://localhost:8102";
const gitServiceBaseUrl = process.env.VITE_GIT_SERVICE_BASE_URL || "http://localhost:8103";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls },
    }),
    quasar(),
  ],
  server: {
    host: "127.0.0.1",
    fs: {
      strict: true,
      allow: [fileURLToPath(new URL(".", import.meta.url))],
    },
    proxy: {
      "/api/predict": {
        target: "https://nlp-api-normativesystems.tnodatalab.nl",
        secure: false,
        changeOrigin: true,
      },
      "/api/wrapUp": {
        target: "https://wrap-up-api-normativesystems.tnodatalab.nl",
        secure: false,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/wrapUp/, ""),
      },
      "/api/unwrap": {
        target: "https://unwrap-api-normativesystems.tnodatalab.nl",
        secure: false,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/unwrap/, ""),
      },
      "/api/serverless/getSources": {
        target: "/.netlify/functions/getAvailableSourcesFromTriply",
        secure: false,
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/.netlify\/functions/, ""),
      },
      "/api/serverless/getSource": {
        target: "/.netlify/functions/getSourceFromTriply",
        secure: false,
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/.netlify\/functions/, ""),
      },
      "/api/serverless/getAvailableTasks": {
        target: "/.netlify/functions/getAvailableTasksFromTriply",
        secure: false,
        changeOrigin: true,
      },
      "/api/serverless/getTask": {
        target: "/.netlify/functions/getTaskFromTriply",
        secure: false,
        changeOrigin: true,
      },
      "/api/serverless/saveTaskAtTriply": {
        target: "/.netlify/functions/saveTask",
        secure: false,
        changeOrigin: true,
      },
      "/api/serverless/saveTaskAtMongo": {
        target: "/.netlify/functions/saveTaskToMongo",
        secure: false,
        changeOrigin: true,
      },
      "/auth": {
        target: authApiBaseUrl,
        secure: false,
        changeOrigin: true,
      },
      "/generate-eflint": {
        target: eflintApiBaseUrl,
        secure: false,
        changeOrigin: true,
      },
      "/execute": {
        target: eflintExecuteBaseUrl,
        secure: false,
        changeOrigin: true,
      },
      "/repl": {
        target: eflintExecuteBaseUrl,
        secure: false,
        changeOrigin: true,
      },
      "/eflint-server": {
        target: eflintServerBaseUrl,
        secure: false,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/eflint-server/, ""),
      },
      "/mongo-api": {
        target: mongoApiBaseUrl,
        secure: false,
        changeOrigin: true,
      },
      "/github-api": {
        target: "https://api.github.com",
        secure: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/github-api/, ""),
      },
      "/git-service": {
        target: gitServiceBaseUrl,
        secure: false,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/git-service/, ""),
      },
    },
  },
});

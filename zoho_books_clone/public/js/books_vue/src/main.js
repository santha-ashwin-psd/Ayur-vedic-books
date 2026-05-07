import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { bootstrapSession } from "./api/session.js";
import "./shell.css";

// Bootstrap the session before mounting so usePermissions() and the API
// client see populated state synchronously after the await.
bootstrapSession().then(() => {
  const app = createApp(App);
  app.use(router);
  app.mount("#books-app");
});

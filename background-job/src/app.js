import express from "express";
import { serve } from "inngest/express";
import { inngest } from "./inngest/client.js";
import { functions } from "./inngest/functions.js";

export function createApp() {
  const app = express();

  app.use(express.json());
  app.use("/api/inngest", serve({ client: inngest, functions }));

  app.get("/health", (_req, res) => {
    res.status(200).json({ status: "ok" });
  });

  return app;
}

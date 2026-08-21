import express from "express";
import { serve } from "inngest/express";
import { inngest } from "./inngest/client.js";
import { functions } from "./inngest/functions.js";
import { createReport, getReport } from "./reports-store.js";

export function createApp() {
  const app = express();

  app.use(express.json());
  app.use("/api/inngest", serve({ client: inngest, functions }));

  app.get("/health", (_req, res) => {
    res.status(200).json({ status: "ok" });
  });

  app.post("/reports", async (req, res, next) => {
    try {
      const topic = typeof req.body.topic === "string" ? req.body.topic.trim() : "";

      if (!topic) {
        res.status(400).json({ error: "topic is required" });
        return;
      }

      const report = createReport(topic);

      if (process.env.DISABLE_INNGEST_SEND !== "1") {
        await inngest.send({
          name: "report/requested",
          data: { id: report.id, topic: report.topic },
        });
      }

      res.status(202).json({ id: report.id, status: report.status });
    } catch (error) {
      next(error);
    }
  });

  app.get("/reports/:id", (req, res) => {
    const report = getReport(req.params.id);

    if (!report) {
      res.status(404).json({ error: "Report not found" });
      return;
    }

    res.status(200).json(report);
  });

  return app;
}

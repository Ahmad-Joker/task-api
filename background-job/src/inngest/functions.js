import { inngest } from "./client.js";
import { failReport, finishReport, getReportSummary } from "../reports-store.js";

export const sayHello = inngest.createFunction(
  { id: "say-hello" },
  { event: "test/hello" },
  async ({ step }) => {
    await step.sleep("wait-five-seconds", "5s");
    return "Hello from the background!";
  },
);

export const makeReport = inngest.createFunction(
  { id: "make-report", retries: 2 },
  { event: "report/requested" },
  async ({ event, step }) => {
    const { id, topic } = event.data;

    await step.sleep("do-the-slow-work", "8s");

    return step.run("build-report", async () => {
      if (topic === "fail") {
        failReport(id, "The report oven is broken!");
        throw new Error("The report oven is broken!");
      }

      const result = `Report for "${topic}": background work completed successfully.`;
      return finishReport(id, result);
    });
  },
);

export const heartbeat = inngest.createFunction(
  { id: "heartbeat" },
  { cron: "* * * * *" },
  async ({ step }) => {
    return step.run("log-report-summary", async () => {
      const summary = getReportSummary();
      const line = `heartbeat: pending=${summary.pending} done=${summary.done} failed=${summary.failed}`;
      console.log(line);
      return line;
    });
  },
);

export const functions = [sayHello, makeReport, heartbeat];

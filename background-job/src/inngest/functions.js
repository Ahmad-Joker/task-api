import { inngest } from "./client.js";
import { finishReport } from "../reports-store.js";

export const sayHello = inngest.createFunction(
  { id: "say-hello" },
  { event: "test/hello" },
  async ({ step }) => {
    await step.sleep("wait-five-seconds", "5s");
    return "Hello from the background!";
  },
);

export const makeReport = inngest.createFunction(
  { id: "make-report" },
  { event: "report/requested" },
  async ({ event, step }) => {
    const { id, topic } = event.data;

    await step.sleep("do-the-slow-work", "8s");

    return step.run("build-report", async () => {
      const result = `Report for "${topic}": background work completed successfully.`;
      return finishReport(id, result);
    });
  },
);

export const functions = [sayHello, makeReport];

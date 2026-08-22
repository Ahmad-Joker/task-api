import { Inngest } from "inngest";

export const inngest = new Inngest({
  id: "report-api",
  isDev: process.env.INNGEST_DEV !== "0",
});

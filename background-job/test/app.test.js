import request from "supertest";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createApp } from "../src/app.js";
import { getReport, resetReports } from "../src/reports-store.js";

beforeEach(() => {
  process.env.DISABLE_INNGEST_SEND = "1";
});

afterEach(() => {
  resetReports();
  delete process.env.DISABLE_INNGEST_SEND;
});

describe("health endpoint", () => {
  it("returns ok", async () => {
    const response = await request(createApp()).get("/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({ status: "ok" });
  });
});

describe("report endpoints", () => {
  it("accepts a report and returns pending status", async () => {
    const response = await request(createApp())
      .post("/reports")
      .send({ topic: "cats" });

    expect(response.status).toBe(202);
    expect(response.body).toMatchObject({ status: "pending" });
    expect(response.body.id).toEqual(expect.any(String));
    expect(getReport(response.body.id)).toMatchObject({
      id: response.body.id,
      topic: "cats",
      status: "pending",
    });
  });

  it("returns 404 for unknown reports", async () => {
    const response = await request(createApp()).get("/reports/nope");

    expect(response.status).toBe(404);
    expect(response.body).toEqual({ error: "Report not found" });
  });
});

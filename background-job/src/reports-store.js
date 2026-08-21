const reports = new Map();

export function createReport(topic) {
  const id = crypto.randomUUID();
  const report = {
    id,
    topic,
    status: "pending",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  reports.set(id, report);
  return report;
}

export function getReport(id) {
  return reports.get(id);
}

export function listReports() {
  return Array.from(reports.values());
}

export function finishReport(id, result) {
  const report = reports.get(id);
  if (!report) return undefined;

  const updated = {
    ...report,
    status: "done",
    result,
    updatedAt: new Date().toISOString(),
  };
  reports.set(id, updated);
  return updated;
}

export function failReport(id, error) {
  const report = reports.get(id);
  if (!report) return undefined;

  const updated = {
    ...report,
    status: "failed",
    error,
    updatedAt: new Date().toISOString(),
  };
  reports.set(id, updated);
  return updated;
}

export function resetReports() {
  reports.clear();
}

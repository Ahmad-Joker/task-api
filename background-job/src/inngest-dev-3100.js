import { spawn } from "node:child_process";

const child = spawn(
  process.execPath,
  ["node_modules/inngest-cli/bin/inngest", "dev", "-u", "http://localhost:3100/api/inngest"],
  { shell: false, stdio: "inherit" },
);

child.on("exit", (code) => {
  process.exit(code ?? 0);
});

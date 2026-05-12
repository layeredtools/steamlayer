import { execFile, ChildProcess } from "child_process";
import path from "path";
import { app } from "electron";


export const BACKEND_PORT = 58732;
export const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

const HEALTH_POLL_INTERVAL_MS = 250;
const HEALTH_POLL_TIMEOUT_MS = 15_000;


interface BackendHandle {
  process: ChildProcess;
  kill: () => void;
}

interface HealthPollOptions {
  intervalMs?: number;
  timeoutMs?: number;
}


function resolveBackendBin(): { bin: string; args: string[]; cwd: string } {
  const repoRoot = path.join(__dirname, "../../../.."); // packages/app/out/main
  if (!app.isPackaged) {
    return {
      bin: path.join(
        repoRoot,
        ".venv",
        "Scripts",
        process.platform === "win32" ? "steamlayer-backend.exe" : "steamlayer-backend"
      ),
      args: ["--port", String(BACKEND_PORT)],
      cwd: repoRoot,
    };
  }

  return {
    bin: path.join(
      process.resourcesPath,
      process.platform === "win32" ? "steamlayer-backend.exe" : "steamlayer-backend"
    ),
    args: ["--port", String(BACKEND_PORT)],
    cwd: process.resourcesPath,
  };
}

/**
 * Polls /health until the backend responds 200 or the timeout elapses.
 * Resolves on success, rejects on timeout.
 */
async function waitForHealth(opts: HealthPollOptions = {}): Promise<void> {
  const interval = opts.intervalMs ?? HEALTH_POLL_INTERVAL_MS;
  const timeout  = opts.timeoutMs  ?? HEALTH_POLL_TIMEOUT_MS;
  const deadline = Date.now() + timeout;

  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (res.ok) return;
    } catch {
      // not ready yet — swallow and retry
    }

    await new Promise<void>((r) => setTimeout(r, interval));
  }

  throw new Error(
    `Backend did not become healthy within ${timeout}ms.`
  );
}

/**
 * Spawns the Python backend and waits until it is healthy.
 * Returns a handle with a `kill()` method for clean shutdown.
 *
 * Throws if the process exits early or the health check times out.
 */
export async function startBackend(): Promise<BackendHandle> {
  const { bin, args, cwd } = resolveBackendBin();

  return new Promise<BackendHandle>((resolve, reject) => {
    const child = execFile(bin, args, { windowsHide: true, cwd });

    if (!app.isPackaged) {
      child.stdout?.on("data", (d: Buffer) => process.stdout.write(`[backend] ${d}`));
      child.stderr?.on("data", (d: Buffer) => process.stderr.write(`[backend] ${d}`));
    }

    child.once("exit", (code) => {
      reject(new Error(`Backend exited early with code ${code}`));
    });

    waitForHealth()
      .then(() => {
        child.removeAllListeners("exit");

        resolve({
          process: child,
          kill: () => {
            if (!child.killed) child.kill();
          },
        });
      })
      .catch(reject);
  });
}

export type { BackendHandle };

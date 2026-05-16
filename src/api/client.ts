/**
 * Shared fetch helper for all backend API clients.
 * Vite dev server proxies /api/* to portal_server.py (port 8001).
 * In production, same-origin assumed.
 */

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly url: string,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface FetchOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
}

export async function apiFetch<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const url = path.startsWith("http") ? path : path;
  const init: RequestInit = {
    method: opts.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    signal: opts.signal,
  };
  if (opts.body !== undefined) {
    init.body = JSON.stringify(opts.body);
  }

  const res = await fetch(url, init);
  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      try {
        body = await res.text();
      } catch {
        body = undefined;
      }
    }
    throw new ApiError(
      `${res.status} ${res.statusText} on ${path}`,
      res.status,
      path,
      body,
    );
  }
  return (await res.json()) as T;
}

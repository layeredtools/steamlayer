let _baseUrl: string | null = null;

async function baseUrl(): Promise<string> {
  if (!_baseUrl) _baseUrl = await window.electron.backendUrl();
  return _baseUrl;
}

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

export async function request<T>(
  method: HttpMethod,
  path: string,
  body?: unknown
): Promise<T> {
  const url = `${await baseUrl()}${path}`;
  const res = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? res.statusText);
  }

  return res.json() as Promise<T>;
}
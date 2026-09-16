import { NextResponse } from "next/server";

// Runtime-configurable API proxy. Forwarding the request at request-time (rather
// than baking a destination into next.config rewrites at build time) means the
// backend URL can be set as a runtime env var (e.g. API_URL=http://api:8000 in
// Docker, or http://localhost:8000 in dev) with no rebuild.
const FALLBACK_API_URL = "http://localhost:8000";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
  "host",
  "content-length",
]);

const ALLOWED_METHODS = new Set(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]);

async function handle(request: Request, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;

  const base = (process.env.API_URL || FALLBACK_API_URL).replace(/\/+$/, "");
  const pathname = path.length ? `/api/v1/${path.map(encodeURIComponent).join("/")}` : "/api/v1";
  const url = new URL(pathname, base);
  url.search = new URL(request.url).search;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const accept = request.headers.get("accept");
  if (accept) headers.set("accept", accept);

  const method = request.method.toUpperCase();
  if (!ALLOWED_METHODS.has(method)) {
    return NextResponse.json({ detail: `method ${method} not allowed` }, { status: 405 });
  }

  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();

  let upstream: Response;
  try {
    upstream = await fetch(url.toString(), {
      method,
      headers,
      body: body === undefined ? undefined : body,
    });
  } catch {
    // Backend unreachable: return a clean error instead of an empty 500 so the
    // UI can show something meaningful (the handler proxies, it does not retry).
    return NextResponse.json(
      { detail: `backend unreachable at ${base}` },
      { status: 502 }
    );
  }

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) responseHeaders.set(key, value);
  });

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const HEAD = handle;
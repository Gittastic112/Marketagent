const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

async function proxyRequest(request: Request, context: RouteContext) {
  const { path } = await context.params;
  const sourceUrl = new URL(request.url);
  const targetPath = path.map(encodeURIComponent).join("/");
  const targetUrl = `${API_BASE_URL}/${targetPath}${sourceUrl.search}`;
  const headers = new Headers(request.headers);
  headers.delete("host");

  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(),
    cache: "no-store"
  });

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers
  });
}

export async function GET(request: Request, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function POST(request: Request, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function PATCH(request: Request, context: RouteContext) {
  return proxyRequest(request, context);
}

export async function DELETE(request: Request, context: RouteContext) {
  return proxyRequest(request, context);
}

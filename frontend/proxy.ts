import { getToken } from "next-auth/jwt";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

function signInRedirect(request: NextRequest, configurationError = false): NextResponse {
  const signInUrl = new URL("/auth/signin", request.url);
  signInUrl.searchParams.set("callbackUrl", `${request.nextUrl.pathname}${request.nextUrl.search}`);
  if (configurationError) {
    signInUrl.searchParams.set("error", "Configuration");
  }
  return NextResponse.redirect(signInUrl);
}

export async function proxy(request: NextRequest): Promise<NextResponse> {
  const secret = process.env.NEXTAUTH_SECRET;
  if (!secret) {
    return signInRedirect(request, true);
  }

  const token = await getToken({ req: request, secret });
  return token ? NextResponse.next() : signInRedirect(request);
}

export const config = {
  matcher: ["/((?!api|auth/signin|_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};

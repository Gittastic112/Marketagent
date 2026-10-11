export type SessionCookie = {
  name: string;
  value: string;
};

const SESSION_COOKIE_NAMES = [
  "__Secure-next-auth.session-token",
  "next-auth.session-token",
  "__Secure-authjs.session-token",
  "authjs.session-token",
] as const;


function tokenForCookieName(cookies: SessionCookie[], cookieName: string): string | null {
  const direct = cookies.find((cookie) => cookie.name === cookieName)?.value;
  if (direct) return direct;

  const chunks = cookies
    .filter((cookie) => cookie.name.startsWith(`${cookieName}.`))
    .map((cookie) => ({
      value: cookie.value,
      index: Number(cookie.name.slice(cookieName.length + 1)),
    }))
    .filter((chunk) => Number.isInteger(chunk.index) && chunk.index >= 0)
    .sort((left, right) => left.index - right.index);

  return chunks.length > 0 ? chunks.map((chunk) => chunk.value).join("") : null;
}


export function findNextAuthSessionToken(cookies: SessionCookie[]): string | null {
  for (const cookieName of SESSION_COOKIE_NAMES) {
    const token = tokenForCookieName(cookies, cookieName);
    if (token) return token;
  }
  return null;
}

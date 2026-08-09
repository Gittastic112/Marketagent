import "server-only";

import { createHmac } from "node:crypto";

export const INTERNAL_USER_HEADER = "x-market-intel-user";
export const INTERNAL_SIGNATURE_HEADER = "x-market-intel-signature";

type AuthenticatedIdentity = {
  id: string;
  email?: string | null;
  name?: string | null;
};

export function createBackendAuthHeaders(
  identity: AuthenticatedIdentity,
  secret = process.env.NEXTAUTH_SECRET,
): Record<string, string> {
  if (!secret) {
    throw new Error("NEXTAUTH_SECRET is required for backend authentication");
  }

  const payload = Buffer.from(
    JSON.stringify({
      sub: identity.id,
      email: identity.email ?? null,
      name: identity.name ?? null,
      iat: Math.floor(Date.now() / 1000),
    }),
    "utf8",
  ).toString("base64url");
  const signature = createHmac("sha256", secret).update(payload, "ascii").digest("hex");

  return {
    [INTERNAL_USER_HEADER]: payload,
    [INTERNAL_SIGNATURE_HEADER]: signature,
  };
}

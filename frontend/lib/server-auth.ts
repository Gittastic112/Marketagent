import "server-only";

import { cookies } from "next/headers";
import { decode } from "next-auth/jwt";

import { findNextAuthSessionToken } from "@/lib/session-cookie";


export type ServerIdentity = {
  id: string;
  email?: string | null;
  name?: string | null;
};


export async function readServerIdentity(secret: string): Promise<ServerIdentity | null> {
  const cookieStore = await cookies();
  const encryptedToken = findNextAuthSessionToken(cookieStore.getAll());
  if (!encryptedToken) return null;

  try {
    const token = await decode({ token: encryptedToken, secret });
    const id = typeof token?.id === "string" ? token.id : token?.sub;
    if (!id) return null;
    return {
      id,
      email: typeof token?.email === "string" ? token.email : null,
      name: typeof token?.name === "string" ? token.name : null,
    };
  } catch {
    return null;
  }
}

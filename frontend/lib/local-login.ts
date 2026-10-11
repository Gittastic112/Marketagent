import { createHash, timingSafeEqual } from "node:crypto";

/** Single-process local login throttle. Fixed-size state, no spoofable IP buckets. */
export function createLocalLoginGuard(limit = 10, windowMs = 60_000) {
  let attempts = 0;
  let windowStart = 0;
  return (username: unknown, password: unknown, expectedUsername: string | undefined,
    expectedPassword: string | undefined, now = Date.now()): boolean => {
    if (now - windowStart >= windowMs) { attempts = 0; windowStart = now; }
    if (++attempts > limit || !expectedUsername || !expectedPassword) return false;
    if (typeof username !== "string" || typeof password !== "string" || username.length > 256 || password.length > 1024) return false;
    const hash = (value: string) => createHash("sha256").update(value).digest();
    const validName = timingSafeEqual(hash(username), hash(expectedUsername));
    const validPassword = timingSafeEqual(hash(password), hash(expectedPassword));
    return validName && validPassword;
  };
}

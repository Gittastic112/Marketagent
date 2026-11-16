"use client";

import { localCallback } from "@/lib/auth-navigation";
import { LogIn } from "lucide-react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useEffect, useState } from "react";

type AuthReadiness = {
  configured: boolean;
  missing: string[];
  mode: "local_single_user";
  production_ready: false;
};

export default function SignInPage() {
  return (
    <Suspense fallback={<main className="page-container" />}>
      <SignInForm />
    </Suspense>
  );
}

function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [readiness, setReadiness] = useState<AuthReadiness | null>(null);
  const [readinessError, setReadinessError] = useState(false);
  const [checkNumber, setCheckNumber] = useState(0);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10_000);
    setReadiness(null);
    setReadinessError(false);
    fetch("/api/auth/readiness", { cache: "no-store", signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Readiness check failed");
        }
        return response.json() as Promise<AuthReadiness>;
      })
      .then((result) => {
        if (active) {
          if (typeof result.configured !== "boolean" || !Array.isArray(result.missing)) throw new Error("Invalid readiness");
          setReadiness(result);
        }
      })
      .catch(() => {
        if (active) {
          setReadinessError(true);
        }
      }).finally(() => clearTimeout(timer));
    return () => {
      active = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [checkNumber]);

  const authUnavailable = readinessError || readiness?.configured !== true;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSubmitting || authUnavailable) return;
    setIsSubmitting(true);
    setError(null);
    const formData = new FormData(event.currentTarget);
    const callbackUrl = localCallback(searchParams.get("callbackUrl"), window.location.origin);
    try {
      const result = await signIn("credentials", {
        redirect: false,
        callbackUrl,
        username: formData.get("username"),
        password: formData.get("password"),
      });
      if (!result?.ok || result.error) {
        setError("Sign-in failed. Check the provided credentials and try again.");
        return;
      }
      router.replace(callbackUrl);
      router.refresh();
    } catch {
      setError("Sign-in could not be confirmed. Your entries are retained; try again when the connection recovers.");
    } finally {
      setIsSubmitting(false);
    }

  }

  return (
    <div className="page-container" style={{ display: "grid", minHeight: "70vh", placeItems: "center" }}>
      <form className="panel" onSubmit={submit} style={{ display: "grid", gap: "16px", maxWidth: "400px", padding: "24px", width: "100%" }}>
        <div>
          <h1 style={{ fontSize: "28px", margin: 0 }}>Sign in</h1>
        </div>
        <div className="field">
          <label htmlFor="username">Username</label>
          <input id="username" name="username" autoComplete="username" required />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input id="password" name="password" type="password" autoComplete="current-password" required />
        </div>
        {readiness?.configured === false ? (
          <p style={{ color: "var(--danger)", margin: 0 }}>
            Local authentication is not configured
            {readiness?.missing.length ? `: ${readiness.missing.join(", ")}` : "."}
          </p>
        ) : null}
        {readinessError ? (
          <p style={{ color: "var(--danger)", margin: 0 }}>
            Unable to verify local authentication configuration.
          </p>
        ) : null}
        {(readinessError || readiness?.configured === false) && <button type="button" onClick={() => setCheckNumber(value => value + 1)}>Check configuration again</button>}
        {error ? <p role="alert" style={{ color: "var(--danger)", margin: 0 }}>{error}</p> : null}
        <button type="submit" disabled={isSubmitting || readiness === null || authUnavailable}>
          <LogIn size={16} />
          {isSubmitting ? "Signing in..." : readinessError ? "Configuration unavailable" : readiness === null ? "Checking configuration..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}

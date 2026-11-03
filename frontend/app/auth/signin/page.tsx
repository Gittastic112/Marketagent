"use client";

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
  const isConfigurationError = searchParams.get("error") === "Configuration";
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [readiness, setReadiness] = useState<AuthReadiness | null>(null);
  const [readinessError, setReadinessError] = useState(false);

  useEffect(() => {
    let active = true;
    fetch("/api/auth/readiness", { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Readiness check failed");
        }
        return response.json() as Promise<AuthReadiness>;
      })
      .then((result) => {
        if (active) {
          setReadiness(result);
        }
      })
      .catch(() => {
        if (active) {
          setReadinessError(true);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const authUnavailable = isConfigurationError || readinessError || readiness?.configured === false;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    const formData = new FormData(event.currentTarget);
    const result = await signIn("credentials", {
      redirect: false,
      username: formData.get("username"),
      password: formData.get("password"),
    });
    if (result?.error) {
      setError("Sign-in failed. Check the provided credentials.");
      setIsSubmitting(false);
      return;
    }
    const callbackUrl = searchParams.get("callbackUrl");
    router.replace(callbackUrl?.startsWith("/") ? callbackUrl : "/");
    router.refresh();
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
        {isConfigurationError || readiness?.configured === false ? (
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
        {error ? <p style={{ color: "var(--danger)", margin: 0 }}>{error}</p> : null}
        <button type="submit" disabled={isSubmitting || readiness === null || authUnavailable}>
          <LogIn size={16} />
          {isSubmitting ? "Signing in..." : readiness === null ? "Checking configuration..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}

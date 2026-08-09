import { NextResponse } from "next/server";

const REQUIRED_LOCAL_AUTH_VARIABLES = [
  "NEXTAUTH_SECRET",
  "LOCAL_AUTH_USERNAME",
  "LOCAL_AUTH_PASSWORD",
] as const;

export async function GET() {
  const configuredByVariable = {
    NEXTAUTH_SECRET: Boolean(process.env.NEXTAUTH_SECRET),
    LOCAL_AUTH_USERNAME: Boolean(process.env.LOCAL_AUTH_USERNAME),
    LOCAL_AUTH_PASSWORD: Boolean(process.env.LOCAL_AUTH_PASSWORD),
  };
  const missing = REQUIRED_LOCAL_AUTH_VARIABLES.filter(
    (name) => !configuredByVariable[name],
  );

  return NextResponse.json(
    {
      configured: missing.length === 0,
      missing,
      mode: "local_single_user",
      production_ready: false,
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}

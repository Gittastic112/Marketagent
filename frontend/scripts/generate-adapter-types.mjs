import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import openapiTS, { astToString } from "openapi-typescript";

const check = process.argv.includes("--check");
if (process.argv.slice(2).some(argument => argument !== "--check")) {
  throw new Error("Usage: node scripts/generate-adapter-types.mjs [--check]");
}
const schema = new URL("../lib/api/generated/adapters.openapi.json", import.meta.url);
const destination = new URL("../lib/api/generated/adapters.ts", import.meta.url);
const header = "/** Generated from adapters.openapi.json. Run npm run generate:adapter-types; do not edit. */\n";
const generated = header + astToString(await openapiTS(schema, { alphabetize: true, defaultNonNullable: false }));

if (check) {
  const temporary = await mkdtemp(join(tmpdir(), "marketagent-adapter-types-"));
  try {
    const regenerated = join(temporary, "adapters.ts");
    await writeFile(regenerated, generated);
    const [expected, actual] = await Promise.all([readFile(destination, "utf8"), readFile(regenerated, "utf8")]);
    if (expected !== actual) {
      throw new Error("Adapter types are stale. Run npm run generate:adapter-types and commit the result.");
    }
    console.log("Adapter types match the committed OpenAPI snapshot.");
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
} else {
  await writeFile(destination, generated);
  console.log("Generated lib/api/generated/adapters.ts from the committed OpenAPI snapshot.");
}

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = fileURLToPath(new URL("../../", import.meta.url));

/** Inspect the same ordered local imports that the CSS compiler receives. */
export function readStyles(file = "app/globals.css", ancestors: string[] = []): string {
  const absolute = path.resolve(frontendRoot, file);
  if (!absolute.startsWith(frontendRoot) || ancestors.includes(absolute)) {
    throw new Error("Stylesheet import leaves the frontend or contains a cycle.");
  }
  return readFileSync(absolute, "utf8").replace(
    /^@import ["'](\.{1,2}\/[^"']+\.css)["'];\s*$/gm,
    (_match, imported: string) => readStyles(
      path.relative(frontendRoot, path.resolve(path.dirname(absolute), imported)),
      [...ancestors, absolute],
    ),
  );
}

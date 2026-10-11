import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import ts from "typescript";

const frontend = fileURLToPath(new URL("../", import.meta.url));
const repository = process.env.REPOSITORY_ROOT || path.dirname(frontend);
const manifest = JSON.parse(readFileSync(path.join(repository, "data/contracts/frontend-backend.json"), "utf8"));
const files = Object.keys(manifest.contracts).map(name => path.join(frontend, `lib/api/${name}.ts`));
const program = ts.createProgram(files, { strict: true, noEmit: true, target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.NodeNext, moduleResolution: ts.ModuleResolutionKind.NodeNext, allowImportingTsExtensions: true });
const checker = program.getTypeChecker();
type Schema = Record<string, any>;

// Check the backend's possible JSON values against each declared consumer type.
// Omitted frontend fields are allowed; a field that is declared must be real.
function accepts(schema: Schema, type: ts.Type, defs: Schema, label: string): boolean {
  if (type.flags & (ts.TypeFlags.Any | ts.TypeFlags.Unknown | ts.TypeFlags.TypeParameter)) return true;
  if (schema.$ref) return accepts(defs[schema.$ref.split("/").at(-1)], type, defs, label);
  if (schema.anyOf) return schema.anyOf.every((part: Schema) => accepts(part, type, defs, label));
  if (schema.enum) return schema.enum.every((value: unknown) => accepts({ const: value, type: typeof value }, type, defs, label));
  if (type.isUnion()) {
    if (schema.type === "boolean" && schema.const === undefined) {
      return [true, false].every(value => accepts({ type: "boolean", const: value }, type, defs, label));
    }
    return type.types.some(part => accepts(schema, part, defs, label));
  }
  if (schema.type === "null") return Boolean(type.flags & ts.TypeFlags.Null);
  if (schema.type === "string") {
    return Boolean(type.flags & ts.TypeFlags.String) || (type.isStringLiteral() && schema.const === type.value);
  }
  if (schema.type === "number" || schema.type === "integer") {
    return Boolean(type.flags & ts.TypeFlags.Number) || (type.isNumberLiteral() && schema.const === type.value);
  }
  if (schema.type === "boolean") {
    if (type.flags & ts.TypeFlags.Boolean) return true;
    return Boolean(type.flags & ts.TypeFlags.BooleanLiteral) && checker.typeToString(type) === String(schema.const);
  }
  if (schema.type === "array") {
    if (!checker.isArrayType(type)) return false;
    return accepts(schema.items, checker.getIndexTypeOfType(type, ts.IndexKind.Number)!, defs, `${label}[]`);
  }
  if (schema.type === "object") {
    if (!(type.flags & ts.TypeFlags.Object)) return false;
    for (const property of checker.getPropertiesOfType(type)) {
      const child = schema.properties?.[property.name];
      if (!child) return false;
      const declared = checker.getTypeOfSymbolAtLocation(property, property.valueDeclaration ?? property.declarations![0]);
      if (!accepts(child, declared, defs, `${label}.${property.name}`)) return false;
    }
    const indexed = checker.getIndexTypeOfType(type, ts.IndexKind.String);
    return !indexed || accepts(schema.additionalProperties ?? {}, indexed, defs, `${label}[key]`);
  }
  return false;
}

test("contract drift rejects incompatible field types and newly possible enum/null values", () => {
  const source = program.getSourceFile(path.join(frontend, "lib/api/daily-brief.ts"))!;
  const declaration = source.statements.find(s => ts.isTypeAliasDeclaration(s) && s.name.text === "DailyBriefSchedule")!;
  const contract = checker.getTypeAtLocation(declaration);
  const property = checker.getPropertyOfType(contract, "generation_mode")!;
  const type = checker.getTypeOfSymbolAtLocation(property, property.declarations![0]);
  assert.equal(accepts({ type: "string", enum: ["deterministic_no_external_ai"] }, type, {}, "mode"), true);
  assert.equal(accepts({ type: "string", enum: ["deterministic_no_external_ai", "unreviewed_ai"] }, type, {}, "mode"), false);
  assert.equal(accepts({ type: "null" }, type, {}, "mode"), false);
  assert.equal(accepts({ type: "number" }, type, {}, "mode"), false);
});

for (const [module, contracts] of Object.entries(manifest.contracts) as Array<[string, Record<string, Schema>]>) {
  const source = program.getSourceFile(path.join(frontend, `lib/api/${module}.ts`))!;
  for (const [name, schema] of Object.entries(contracts)) {
    test(`${module}.${name} accepts its backend wire contract, including nulls, aliases and enums`, () => {
      const declaration = source.statements.find(s => (ts.isTypeAliasDeclaration(s) || ts.isInterfaceDeclaration(s)) && s.name.text === name);
      assert.ok(declaration, `Missing frontend contract ${name}`);
      const type = checker.getTypeAtLocation(declaration);
      const defs = schema.$defs ?? {};
      // Name the individual field on failure instead of hiding it in a huge diff.
      for (const property of checker.getPropertiesOfType(type)) {
        assert.ok(schema.properties?.[property.name], `${name}.${property.name} does not exist on the backend`);
        const declared = checker.getTypeOfSymbolAtLocation(property, property.valueDeclaration ?? property.declarations![0]);
        assert.ok(accepts(schema.properties[property.name], declared, defs, property.name), `${name}.${property.name}: backend JSON is not covered by ${checker.typeToString(declared)}`);
      }
    });
  }
}

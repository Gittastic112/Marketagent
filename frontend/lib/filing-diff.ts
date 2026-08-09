export type FilingDiffSegment = {
  kind: "equal" | "add" | "remove";
  text: string;
};

const TOKEN_PATTERN = /(<ins class="diff-add">|<\/ins>|<del class="diff-remove">|<\/del>)/g;

function decodeEscapedText(value: string): string {
  return value
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&quot;", '"')
    .replaceAll("&#x27;", "'")
    .replaceAll("&amp;", "&");
}

export function parseFilingDiff(diffHtml: string): FilingDiffSegment[] {
  const segments: FilingDiffSegment[] = [];
  let kind: FilingDiffSegment["kind"] = "equal";
  let cursor = 0;

  for (const match of diffHtml.matchAll(TOKEN_PATTERN)) {
    const index = match.index;
    if (index > cursor) {
      segments.push({ kind, text: decodeEscapedText(diffHtml.slice(cursor, index)) });
    }

    const token = match[0];
    if (token === '<ins class="diff-add">' && kind === "equal") {
      kind = "add";
    } else if (token === '<del class="diff-remove">' && kind === "equal") {
      kind = "remove";
    } else if ((token === "</ins>" && kind === "add") || (token === "</del>" && kind === "remove")) {
      kind = "equal";
    } else {
      segments.push({ kind, text: token });
    }
    cursor = index + token.length;
  }

  if (cursor < diffHtml.length) {
    segments.push({ kind, text: decodeEscapedText(diffHtml.slice(cursor)) });
  }

  return segments;
}

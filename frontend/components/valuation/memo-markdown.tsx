"use client";

import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Root, RootContent, Text } from "mdast";
import { memoLink, memoSourceAnchor } from "@/lib/valuation-memo";

/** Transform source markers in prose, leaving code blocks and inline code untouched. */
function sourceCitations(sourceIds: readonly string[], prefix: string) {
  return () => (tree: Root) => {
    function visit(parent: { children: RootContent[] }) {
      parent.children = parent.children.flatMap(node => {
        if (node.type === "text") {
          const parts: RootContent[] = [];
          const value = (node as Text).value;
          let offset = 0;
          for (const match of value.matchAll(/\[source_id:([^\]\n]+)\]/g)) {
            if (match.index! > offset) parts.push({ type: "text", value: value.slice(offset, match.index) });
            const index = sourceIds.indexOf(match[1]);
            parts.push(index < 0
              ? { type: "text", value: `${match[0]} (unresolved citation)` }
              : { type: "link", url: `#${memoSourceAnchor(prefix, index)}`, children: [{ type: "text", value: match[0] }] });
            offset = match.index! + match[0].length;
          }
          if (offset === 0) return [node];
          if (offset < value.length) parts.push({ type: "text", value: value.slice(offset) });
          return parts;
        }
        if ("children" in node && node.type !== "link" && node.type !== "linkReference") {
          visit(node as { children: RootContent[] });
        }
        return [node];
      });
    }
    visit(tree);
  };
}

export function MemoMarkdown({ markdown, sourceIds, sourceAnchorPrefix }: {
  markdown: string; sourceIds: readonly string[]; sourceAnchorPrefix: string;
}) {
  return <div className="memo-markdown" aria-label="Memo text">
    <Markdown
      skipHtml
      remarkPlugins={[remarkGfm, sourceCitations(sourceIds, sourceAnchorPrefix)]}
      urlTransform={url => memoLink(url, sourceIds, sourceAnchorPrefix) ?? ""}
      components={{
        a: ({ href, children }) => href
          ? <a href={href} {...(href.startsWith("#") ? {} : { target: "_blank", rel: "noopener noreferrer" })}>{children}</a>
          : <span className="memo-unresolved-link">{children} (unavailable link)</span>,
        // Generated remote images are neither source evidence nor an authorized remote request.
        img: ({ alt }) => <span className="basis-note">Image omitted{alt ? `: ${alt}` : ""}.</span>,
        table: ({ children }) => <div className="table-wrap" role="region" aria-label="Memo table" tabIndex={0}><table>{children}</table></div>,
      }}
    >{markdown}</Markdown>
  </div>;
}

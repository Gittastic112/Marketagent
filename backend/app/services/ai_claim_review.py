"""Bounded literal checks that guide human review, never semantic certification."""
import re
from decimal import Decimal, InvalidOperation

MARKER = re.compile(r"\[source_id:([^\]]+)\]")
NUMBER = re.compile(r"(?<![\w.])(?:FY\s*)?([+-]?\d[\d,]*(?:\.\d+)?)\s*(%|percent\b)?", re.I)
YEAR = re.compile(r"\b(?:FY\s*)?((?:19|20)\d{2})\b", re.I)
INSTRUCTION = re.compile(r"\b(?:ignore (?:all |the )?(?:previous|prior|system) instructions|system prompt|you are (?:an? )?assistant|claim (?:that )?\w+ (?:was|is)|override (?:the )?instructions)\b", re.I)
INFERENCE = re.compile(r"\b(?:permanent|guarantees?|caused by|proves that|will always)\b", re.I)


def _numbers(text: str) -> set[tuple[str, str]]:
    result = set()
    for match in NUMBER.finditer(text):
        try:
            result.add((str(Decimal(match[1].replace(",", "")).normalize()), "%" if match[2] else "number"))
        except InvalidOperation:
            continue
    return result


def review_claim_literals(text: str, citations: list[dict]) -> dict:
    """Compare each marker's preceding claim with validated quotes for that source.

    Literal overlap cannot align accounting units, calculations, causation or
    periods. Multiple periods are explicitly flagged, even if all tokens match.
    No source instructions are executed and no remote model is called.
    """
    quotes = {}
    for citation in citations:
        if citation.get("status") == "valid":
            quotes.setdefault(str(citation.get("source_id")), []).append(str(citation.get("quote") or ""))
    truncated = len(text) > 100_000
    scanned = text[:100_000]
    claims, previous_end, previous_claim = [], 0, ""
    for index, marker in enumerate(MARKER.finditer(scanned)):
        if index >= 100:
            truncated = True
            break
        preceding = scanned[previous_end:marker.start()].strip()
        # Adjacent markers refer to the same preceding claim, not an empty one.
        claim = preceding if preceding.strip(" ,;.") else previous_claim
        previous_end, previous_claim = marker.end(), claim
        source_id = marker[1].strip()
        passages = quotes.get(source_id, [])
        flags = []
        if not passages:
            flags.append({"code": "support_unavailable", "message": "This claim has no validated exact passage to compare."})
        else:
            support = "\n".join(passages)
            missing = _numbers(claim) - _numbers(support)
            if missing:
                flags.append({"code": "numeric_literals_unmatched", "message": "Some claim numbers are absent from the cited passages. Check the amount, sign, percentage, units and any separate calculation."})
            if _numbers(claim) and len(set(YEAR.findall(support))) > 1:
                flags.append({"code": "multiple_source_periods", "message": "The passages contain multiple years. Confirm each amount belongs to the period claimed."})
            if INSTRUCTION.search(support):
                flags.append({"code": "source_instruction_text", "message": "The cited text contains instruction-like language. It is untrusted source content, not evidence for following those instructions."})
        if INFERENCE.search(claim):
            flags.append({"code": "inference_requires_review", "message": "Review the causal or durability claim separately from the quoted fact."})
        claims.append({"source_id": source_id, "claim_text": claim[-2000:], "flags": flags})
    return {"version": "claim-literal-review-v1", "claims": claims, "truncated": truncated,
            "flag_count": sum(len(claim["flags"]) for claim in claims),
            "requires_review_notes": truncated or any(claim["flags"] for claim in claims),
            "scope": "Numeric literal overlap, multiple-period and instruction/inference cues only. Absence of flags is not factual or semantic validation."}

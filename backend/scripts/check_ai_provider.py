"""Send one fixed Gemini test prompt and persist a sanitized Processing Run."""
import argparse
import json

from app.db.session import SessionLocal
from app.services.ai_provider_probe import probe_gemini


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Optional explicit model override for this probe only.")
    args = parser.parse_args()
    with SessionLocal() as db:
        try:
            result = probe_gemini(db, model_name=args.model)
        except ValueError:
            print(json.dumps({"status": "failed", "failure_code": "INVALID_MODEL_CONFIGURATION"}))
            return 2
    print(json.dumps(result))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())

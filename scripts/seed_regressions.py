import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import SessionLocal
from app.services.regression_seed_service import sync_source_backed_regression_coefficients


def seed_regression_coefficients() -> dict[str, int]:
    db = SessionLocal()
    try:
        result = sync_source_backed_regression_coefficients(db)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    summary = seed_regression_coefficients()
    print(
        "Synchronized source-backed January 2025 regressions: "
        f"{summary['models']} models, {summary['coefficients']} coefficients, "
        f"{summary['created']} created, {summary['updated']} updated, "
        f"{summary['deleted']} obsolete removed, {summary['unchanged']} unchanged."
    )

from app.db.session import SessionLocal
from app.services.seed_data import seed_sample_data


def main() -> None:
    with SessionLocal() as db:
        result = seed_sample_data(db)
    print(result)


if __name__ == "__main__":
    main()

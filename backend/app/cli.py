from app.db.session import SessionLocal
from app.db.seeds import seed_all


def run_seed() -> None:
    session = SessionLocal()
    try:
        seed_all(session)
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()

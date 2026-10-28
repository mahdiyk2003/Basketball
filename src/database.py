from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "basketball.db"

engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}",
    echo=False
)


class Base(DeclarativeBase):
    pass


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)


def create_tables():
    import src.models

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print(f"Database created at: {DB_PATH}")
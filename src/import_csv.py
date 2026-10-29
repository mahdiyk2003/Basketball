
from pathlib import Path

import pandas as pd

from src.database import SessionLocal
from src.models import TournamentInfo


def import_tournament_info():
    project_dir = Path(__file__).resolve().parent.parent
    csv_path = project_dir / "data" / "nba_seasons.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"فایل CSV پیدا نشد: {csv_path}"
        )

    encodings = ["utf-8-sig", "cp1252", "latin1"]

    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            print(f"CSV encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("کدگذاری فایل CSV قابل تشخیص نیست.")

    df.columns = df.columns.str.strip()

    df = df.rename(columns={
        "Season id": "season_id",
        "Season": "season",
        "Champion": "champion",
        "MVP candidates": "mvp_candidates",
    })

    required_columns = {
        "season_id",
        "season",
        "champion",
        "mvp_candidates",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"ستون‌های زیر در CSV پیدا نشدند: "
            f"{sorted(missing_columns)}\n"
            f"ستون‌های موجود: {df.columns.tolist()}"
        )

    df = df.dropna(
        subset=["season_id", "season"]
    ).copy()

    df["season_id"] = pd.to_numeric(
        df["season_id"], errors="raise"
    ).astype(int)

    df["season"] = df["season"].astype(str).str.strip()

    for column in ["champion", "mvp_candidates"]:
        df[column] = df[column].where(
            df[column].notna(), None
        )

        df[column] = df[column].map(
            lambda value: (
                value.strip()
                if isinstance(value, str)
                else value
            )
        )

    if df["season_id"].duplicated().any():
        raise ValueError(
            "شناسه فصل در فایل CSV تکراری است."
        )

    if df["season"].duplicated().any():
        raise ValueError(
            "نام فصل در فایل CSV تکراری است."
        )

    with SessionLocal() as session:
        try:
            inserted = 0
            updated = 0

            for _, row in df.iterrows():
                season_id = int(row["season_id"])

                tournament = session.get(
                    TournamentInfo, season_id
                )

                values = {
                    "season": row["season"],
                    "champion": row["champion"],
                    "mvp_candidates": row["mvp_candidates"],
                }

                if tournament is None:
                    tournament = TournamentInfo(
                        season_id=season_id,
                        **values,
                    )
                    session.add(tournament)
                    inserted += 1
                else:
                    for column, value in values.items():
                        setattr(tournament, column, value)

                    updated += 1

            session.commit()

            print("انتقال اطلاعات با موفقیت انجام شد.")
            print(f"فصل‌های جدید: {inserted}")
            print(f"فصل‌های به‌روزرسانی‌شده: {updated}")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    import_tournament_info()


from pathlib import Path
import pandas as pd
from src.database import SessionLocal
from src.models import TeamInfo


def import_teams():
    project_dir = Path(__file__).resolve().parent.parent
    csv_path = project_dir / "data" / "teams_basic_info.csv"

    encodings = ["utf-8-sig", "cp1252", "latin1", "cp1256"]

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

    df = df.rename(columns={"Team id": "team_id", "Team": "team_name", "Founded Year": "founded_year"})

    required_columns = {"team_id", "team_name", "founded_year"}

    if not required_columns.issubset(df.columns):
        raise ValueError(
            f"ستون‌های موردنیاز پیدا نشدند. "
            f"ستون‌های فایل: {df.columns.tolist()}"
        )

    df = df.dropna(subset=["team_id", "team_name"]).copy()

    df["team_id"] = pd.to_numeric(df["team_id"], errors="raise").astype(int)

    df["team_name"] = df["team_name"].astype(str).str.strip()

    df["founded_year"] = pd.to_numeric(df["founded_year"], errors="raise").astype("Int64")
    df = df[df["team_name"] != ""]

    if df["team_id"].duplicated().any():
        raise ValueError("شناسه تیم در فایل CSV تکراری است.")

    with SessionLocal() as session:
        try:
            inserted = 0
            updated = 0

            for _, row in df.iterrows():
                team_id = int(row["team_id"])

                founded_year = (
                    int(row["founded_year"])
                    if pd.notna(row["founded_year"])
                    else None
                )

                team = session.get(TeamInfo, team_id)

                if team is None:
                    team = TeamInfo(team_id=team_id, team_name=row["team_name"], founded_year=founded_year)
                    session.add(team)
                    inserted += 1

                else:
                    team.team_name = row["team_name"]
                    team.founded_year = founded_year
                    updated += 1

            session.commit()

            print("انتقال انجام شد")
            print(f"تعداد تیم‌های جدید: {inserted}")
            print(f"تعداد تیم‌های به‌روزرسانی‌شده: {updated}")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    import_teams()

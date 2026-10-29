
from pathlib import Path
import pandas as pd
from sqlalchemy import select

from src.database import SessionLocal
from src.models import TeamStats


def import_team_stats():
    project_dir = Path(__file__).resolve().parent.parent
    csv_path = project_dir / "data" / "All_Teams_Main.csv"

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
        "season id": "season_id",
        "team id": "team_id",
        "W/L%": "win_loss_pct",
        "SRS": "simple_rating_system",
        "Rel Pace": "relative_pace",
        "Rel ORtg": "relative_offensive_rating",
        "Rel DRtg": "relative_defensive_rating",
        "Finish": "finish",
    })

    required_columns = {
        "season_id",
        "team_id",
        "win_loss_pct",
        "simple_rating_system",
        "relative_pace",
        "relative_offensive_rating",
        "relative_defensive_rating",
        "finish",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"ستون‌های زیر در CSV پیدا نشدند: {sorted(missing_columns)}\n"
            f"ستون‌های موجود: {df.columns.tolist()}"
        )

    df = df.dropna(subset=["season_id", "team_id"]).copy()

    df["season_id"] = pd.to_numeric(df["season_id"], errors="raise").astype(int)

    df["team_id"] = pd.to_numeric(df["team_id"], errors="raise").astype(int)

    numeric_columns = ["win_loss_pct", "simple_rating_system", "relative_pace", "relative_offensive_rating", "relative_defensive_rating",]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="raise")

    df["finish"] = df["finish"].where(df["finish"].notna(), None)

    if df.duplicated(subset=["team_id", "season_id"]).any():
        raise ValueError("برای یک تیم و فصل، رکورد تکراری در فایل CSV وجود دارد.")

    with SessionLocal() as session:
        try:
            inserted = 0
            updated = 0

            for _, row in df.iterrows():
                team_id = int(row["team_id"])
                season_id = int(row["season_id"])

                statement = select(TeamStats).where(TeamStats.team_id == team_id, TeamStats.season_id == season_id,)
                record = session.scalar(statement)
                values = {
                    "win_loss_pct": (
                        float(row["win_loss_pct"])
                        if pd.notna(row["win_loss_pct"])
                        else None
                    ),
                    "simple_rating_system": (
                        float(row["simple_rating_system"])
                        if pd.notna(row["simple_rating_system"])
                        else None
                    ),
                    "relative_pace": (
                        float(row["relative_pace"])
                        if pd.notna(row["relative_pace"])
                        else None
                    ),
                    "relative_offensive_rating": (
                        float(row["relative_offensive_rating"])
                        if pd.notna(row["relative_offensive_rating"])
                        else None
                    ),
                    "relative_defensive_rating": (
                        float(row["relative_defensive_rating"])
                        if pd.notna(row["relative_defensive_rating"])
                        else None
                    ),
                    "finish": (
                        str(row["finish"])
                        if pd.notna(row["finish"])
                        else None
                    ),
                }

                if record is None:
                    record = TeamStats(team_id=team_id, season_id=season_id, **values)
                    session.add(record)
                    inserted += 1
                else:
                    for column, value in values.items():
                        setattr(record, column, value)
                    updated += 1

            session.commit()

            print("انتقال اطلاعات با موفقیت انجام شد.")
            print(f"رکوردهای جدید: {inserted}")
            print(f"رکوردهای به‌روزرسانی‌شده: {updated}")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    import_team_stats()


from pathlib import Path
import pandas as pd
from src.database import SessionLocal
from src.models import PlayerStats


def import_player_stats():
    project_dir = Path(__file__).resolve().parent.parent
    csv_path = project_dir / "data" / "nba_totals.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"فایل CSV پیدا نشد: {csv_path}")

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
        "player id": "player_id",
        "games": "games_played",
        "mp": "minutes_played",
        "fg": "field_goals",
        "fga": "field_goal_attempts",
        "fg3": "three_point_field_goals",
        "fg3a": "three_point_attempts",
        "fg2": "two_point_field_goals",
        "fg2a": "two_point_attempts",
        "efg_pct": "effective_field_goal_pct",
        "ft": "free_throws",
        "fta": "free_throw_attempts",
        "trb": "total_rebounds",
        "ast": "assists",
        "stl": "steals",
        "blk": "blocks",
        "tov": "turnovers",
        "pf": "personal_fouls",
        "pts": "points",
        "position id": "position_id",
        "team id": "team_id",
        "season id": "season_id",
    })

    required_columns = {
        "player_id",
        "games_played",
        "minutes_played",
        "field_goals",
        "field_goal_attempts",
        "three_point_field_goals",
        "three_point_attempts",
        "two_point_field_goals",
        "two_point_attempts",
        "effective_field_goal_pct",
        "free_throws",
        "free_throw_attempts",
        "total_rebounds",
        "assists",
        "steals",
        "blocks",
        "turnovers",
        "personal_fouls",
        "points",
        "position_id",
        "team_id",
        "season_id",
        "awards",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"ستون‌های زیر در CSV پیدا نشدند: "
            f"{sorted(missing_columns)}\n"
            f"ستون‌های موجود: {df.columns.tolist()}"
        )

    key_columns = ["player_id", "team_id", "season_id", "position_id"]

    df = df.dropna(subset=key_columns).copy()

    for column in key_columns:
        df[column] = pd.to_numeric(df[column], errors="raise").astype(int)

    numeric_columns = [
        "games_played",
        "minutes_played",
        "field_goals",
        "field_goal_attempts",
        "three_point_field_goals",
        "three_point_attempts",
        "two_point_field_goals",
        "two_point_attempts",
        "effective_field_goal_pct",
        "free_throws",
        "free_throw_attempts",
        "total_rebounds",
        "assists",
        "steals",
        "blocks",
        "turnovers",
        "personal_fouls",
        "points",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="raise")

    if df.duplicated(
        subset=["player_id", "team_id", "season_id"]).any():
        raise ValueError("برای ترکیب بازیکن، تیم و فصل رکورد تکراری وجود دارد.")

    awards = pd.to_numeric(df["awards"], errors="raise")

    df["mvp_candidate"] = awards.eq(1)

    with SessionLocal() as session:
        try:
            inserted = 0
            updated = 0

            for _, row in df.iterrows():
                player_id = int(row["player_id"])
                team_id = int(row["team_id"])
                season_id = int(row["season_id"])

                record = session.query(PlayerStats).filter_by(
                    player_id=player_id,
                    team_id=team_id,
                    season_id=season_id,).first()

                values = {
                    column: (
                        row[column]
                        if pd.notna(row[column])
                        else None
                    )
                    for column in numeric_columns
                }

                values["mvp_candidate"] = bool(row["mvp_candidate"])

                for column, value in values.items():
                    if value is not None and pd.notna(value):
                        if column in {
                            "games_played",
                            "field_goals",
                            "field_goal_attempts",
                            "three_point_field_goals",
                            "three_point_attempts",
                            "two_point_field_goals",
                            "two_point_attempts",
                            "free_throws",
                            "free_throw_attempts",
                            "total_rebounds",
                            "personal_fouls",
                            "points",
                        }:
                            values[column] = int(value)
                        elif column != "mvp_candidate":
                            values[column] = float(value)

                if record is None:
                    record = PlayerStats(
                        player_id=player_id,
                        team_id=team_id,
                        season_id=season_id,
                        position_id=int(row["position_id"]),
                        **values)
                    session.add(record)
                    inserted += 1
                else:
                    record.position_id = int(row["position_id"])

                    for column, value in values.items():
                        setattr(record, column, value)

                    updated += 1

            session.commit()

            print("انتقال انجام شد")
            print(f"رکوردهای جدید: {inserted}")
            print(f"رکوردهای به‌روزرسانی‌شده: {updated}")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    import_player_stats()

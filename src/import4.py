
from pathlib import Path
import pandas as pd
from src.database import SessionLocal
from src.models import PlayerInfo


def import_player_info():
    project_dir = Path(__file__).resolve().parent.parent
    csv_path = project_dir / "data" / "nba_players.csv"

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

    df = df.rename(columns={"player id": "player_id", "player_name": "name", "born_date": "birth_date"})

    required_columns = {"player_id", "name", "height", "weight", "birth_date", "experience"}

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"ستون‌های زیر در CSV پیدا نشدند: "
            f"{sorted(missing_columns)}\n"
            f"ستون‌های موجود: {df.columns.tolist()}"
        )

    df = df.dropna(subset=["player_id", "name"]).copy()

    df["player_id"] = pd.to_numeric(df["player_id"], errors="raise").astype(int)

    df["name"] = df["name"].astype(str).str.strip()

    for column in ["height", "weight"]:
        df[column] = pd.to_numeric(df[column], errors="raise")

    experience_text = (
        df["experience"].astype("string").str.strip())

    df["experience"] = pd.to_numeric(experience_text.str.extract(r"(\d+)")[0],errors="coerce").astype("Int64")

    df["birth_date"] = df["birth_date"].where(df["birth_date"].notna(), None)

    df["birth_date"] = df["birth_date"].map(
        lambda value: (str(value).strip()if pd.notna(value)else None))

    if df["player_id"].duplicated().any():
        raise ValueError("شناسه بازیکن در فایل CSV تکراری است.")

    with SessionLocal() as session:
        try:
            inserted = 0
            updated = 0

            for _, row in df.iterrows():
                player_id = int(row["player_id"])

                player = session.get(PlayerInfo, player_id)

                values = {
                    "name": row["name"],
                    "height": (
                        float(row["height"])
                        if pd.notna(row["height"])
                        else None
                    ),
                    "weight": (
                        float(row["weight"])
                        if pd.notna(row["weight"])
                        else None
                    ),
                    "birth_date": row["birth_date"],
                    "experience": (
                        int(row["experience"])
                        if pd.notna(row["experience"])
                        else None
                    ),
                }

                if player is None:
                    player = PlayerInfo(
                        player_id=player_id,
                        **values,
                    )
                    session.add(player)
                    inserted += 1
                else:
                    for column, value in values.items():
                        setattr(player, column, value)

                    updated += 1

            session.commit()

            print("انتقال انجام شد")
            print(f"بازیکنان جدید: {inserted}")
            print(f"بازیکنان به‌روزرسانی‌شده: {updated}")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    import_player_info()

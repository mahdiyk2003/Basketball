
from pathlib import Path
import pandas as pd
from sqlalchemy import select
from src.database import SessionLocal, create_tables
from src.models import PositionInfo

# مسیر فایل CSV
PROJECT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_DIR / "data" / "positions.csv"


def import_positions():
    # اطمینان از وجود جدول‌ها
    create_tables()

    # خواندن CSV
    df = pd.read_csv(CSV_PATH)

    # حذف فاصله‌های اضافی از نام ستون‌ها
    df.columns = df.columns.str.strip()

    # تطبیق نام ستون‌ها با ستون‌های مدل
    df = df.rename(columns={
        "position id": "position_id",
        "position name": "position_name"
    })

    # بررسی ستون‌های موردنیاز
    required_columns = {"position_id", "position_name"}
    if not required_columns.issubset(df.columns):
        raise ValueError(
            f"ستون‌های موردنیاز پیدا نشدند. ستون‌های فایل: {df.columns.tolist()}"
        )

    # حذف ردیف‌های ناقص و تکراری
    df = df.dropna(subset=["position_id", "position_name"])
    df["position_id"] = pd.to_numeric(
        df["position_id"], errors="raise"
    ).astype(int)
    df["position_name"] = df["position_name"].astype(str).str.strip()
    df = df[df["position_name"] != ""]
    df = df.drop_duplicates(subset=["position_id"])
    
    # انتقال به دیتابیس
    with SessionLocal() as session:
        try:
            for _, row in df.iterrows():
                existing = session.get(
                    PositionInfo, int(row["position_id"])
                )

                if existing is None:
                    session.add(
                        PositionInfo(
                            position_id=int(row["position_id"]),
                            position_name=row["position_name"]
                        )
                    )
                else:
                    # اگر شناسه وجود دارد، نام آن را به‌روز می‌کنیم
                    existing.position_name = row["position_name"]

            session.commit()
            print(f"{len(df)} ردیف از positions.csv پردازش شد.")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    import_positions()

# src/data_manager.py

import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from .utils import calculate_age_from_dob


# PostgreSQL Configuration

PG_CONFIG = {
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "019604"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "icorpdash"),
}


# =========================
# Create Engine


def get_pg_engine():
    try:
        engine = create_engine(
            f"postgresql+psycopg2://{PG_CONFIG['user']}:{PG_CONFIG['password']}"
            f"@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}",
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        # ทดสอบการเชื่อมต่อ
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        print(f"[ERROR] สร้าง engine ไม่สำเร็จ: {e}")
        return None


# Load Data from PostgreSQL
# โหลดและประมวลผลข้อมูลสมาชิกจาก PostgreSQL


def load_data() -> pd.DataFrame:
    engine = get_pg_engine()
    if engine is None:
        print("[WARNING] ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
        return pd.DataFrame()

    try:
        with engine.connect() as conn:
            df = pd.read_sql("SELECT * FROM members", conn)
    except SQLAlchemyError as e:
        print(f"[ERROR] โหลดข้อมูลไม่สำเร็จ: {e}")
        return pd.DataFrame()
    finally:
        engine.dispose()

    if df.empty:
        print("[INFO] ไม่พบข้อมูลในตาราง members")
        return df

    # ทำความสะอาดข้อมูลรายได้
    if "income" in df.columns:
        df["Income_Clean"] = pd.to_numeric(
            df["income"].astype(str).str.replace(",", "", regex=False), errors="coerce"
        )

    # คำนวณอายุและช่วงอายุ
    if "dob" in df.columns:
        df["Age"] = df["dob"].apply(calculate_age_from_dob)
        df["Age_Group"] = pd.cut(
            df["Age"],
            bins=[0, 20, 30, 40, 50, 60, 120],
            labels=["<20", "20-29", "30-39", "40-49", "50-59", "60+"],
            include_lowest=True,
        )

    return df


# Prepare Data for Export


def prepare_df_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """เตรียม DataFrame สำหรับ export โดยจัดรูปแบบคอลัมน์"""
    if df.empty:
        return df

    df = df.copy()

    # จัดรูปแบบรายได้
    if "Income_Clean" in df.columns:
        df["income"] = df["Income_Clean"].apply(
            lambda x: f"{x:,.0f}" if pd.notna(x) else ""
        )

    # ลบคอลัมน์ชั่วคราว
    temp_cols = ["Income_Clean", "Age", "Age_Group"]
    df.drop(columns=[c for c in temp_cols if c in df.columns], inplace=True)

    return df


# Test Connection


def test_connection() -> bool:
    engine = get_pg_engine()
    if engine is None:
        return False

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM members"))
            count = result.scalar()
            print(f"[INFO] เชื่อมต่อสำเร็จ พบสมาชิก {count} รายการ")
            return True
    except Exception as e:
        print(f"[ERROR] ทดสอบการเชื่อมต่อล้มเหลว: {e}")
        return False
    finally:
        engine.dispose()


if __name__ == "__main__":
    # ทดสอบการเชื่อมต่อและโหลดข้อมูล
    if test_connection():
        df = load_data()
        print(f"[INFO] โหลดข้อมูล {len(df)} รายการ")
        if not df.empty:
            print("\nตัวอย่างข้อมูล 5 แถวแรก:")
            print(df.head())

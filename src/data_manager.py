import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from .utils import calculate_age_from_dob
# 🛠️ ปลดคอมเมนต์เรียบร้อยแล้วเพื่อให้ระบบดึง Logic มาใช้ได้
from .scoring_logic import CreditScoreCalculator

# PostgreSQL Configuration
PG_CONFIG = {
    "user": os.getenv("DB_USER", "myuser"),
    "password": os.getenv("DB_PASSWORD", "mypassword"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "mydatabase"),
}

def get_pg_engine():
    try:
        engine = create_engine(
            f"postgresql+psycopg2://{PG_CONFIG['user']}:{PG_CONFIG['password']}"
            f"@{PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}",
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        return engine
    except Exception as e:
        print(f"[ERROR] สร้าง engine ไม่สำเร็จ: {e}")
        return None

# ==================================================
# ส่วนจัดการข้อมูล Credit Score
# ==================================================

def get_full_member_data(national_id: str):
    """ดึงข้อมูลเชิงลึกจากหลายตารางเพื่อใช้ในการแสดงผลและคำนวณ"""
    engine = get_pg_engine()
    if engine is None: return None
    try:
        with engine.connect() as conn:
            # ดึงข้อมูลจากทุกตารางที่เกี่ยวข้องกับการคำนวณ (Customers, Accounts, History, Summary)
            query = text("""
                SELECT 
                    c.*, 
                    a.account_number, a.monthly_payment, a.account_status,
                    h.payment_performance_pct, h.installments_overdue, 
                    h.late_payment_count_12m, h.late_payment_count_24m,
                    s.credit_utilization_rate, s.total_accounts, s.active_accounts, 
                    s.oldest_account_months, s.inquiries_6m, s.inquiries_12m,
                    sc.credit_score, sc.credit_rating
                FROM credit_scoring.customers c
                LEFT JOIN credit_scoring.credit_accounts a ON c.customer_id = a.customer_id
                LEFT JOIN credit_scoring.payment_history h ON c.customer_id = h.customer_id
                LEFT JOIN credit_scoring.credit_summary s ON c.customer_id = s.customer_id
                LEFT JOIN credit_scoring.credit_scores sc ON c.customer_id = sc.customer_id
                WHERE c.national_id = :nid 
                LIMIT 1
            """)
            df = pd.read_sql(query, conn, params={"nid": str(national_id).strip()})
            
            if df.empty: 
                return None
            
            # จัดการค่า NaN ให้เป็น "-" สำหรับ UI แต่เก็บค่าจริงไว้คำนวณ
            return {k: (v if pd.notna(v) else "-") for k, v in df.iloc[0].to_dict().items()}
    except Exception as e:
        print(f"[ERROR] get_full_member_data: {e}")
        return None

def get_member_profile(national_id: str):
    """ฟังก์ชันหลักสำหรับหน้า UI: ดึงข้อมูลและคำนวณคะแนนทันทีหากยังไม่มี"""
    data = get_full_member_data(national_id)
    
    if not data:
        return None

    # ตรวจสอบว่าต้องคำนวณใหม่หรือไม่ (ถ้าไม่มีคะแนนใน DB)
    if data.get('credit_score') == "-" or data.get('credit_score') is None:
        try:
            calculator = CreditScoreCalculator()
            
            # เตรียมข้อมูลดิบ (แปลง "-" เป็น 0 หรือค่าที่เหมาะสมสำหรับการคำนวณ)
            calc_input = {}
            for k, v in data.items():
                if v == "-":
                    # กำหนด Default สำหรับตัวแปรสำคัญ
                    if k == 'payment_performance_pct': calc_input[k] = 100
                    else: calc_input[k] = 0
                else:
                    calc_input[k] = v
            
            # 🛠️ เรียกใช้ฟังก์ชัน .calculate_all() ให้ตรงกับใน scoring_logic.py
            result = calculator.calculate_all(calc_input)
            
            # อัปเดตข้อมูลที่จะส่งคืนให้ UI
            data.update({
                'credit_score': result.get('credit_score'),
                'credit_rating': result.get('credit_rating'),
                'score_breakdown': result.get('breakdown', {})
            })
            
            # บันทึกคะแนนลง Database อัตโนมัติ
            _save_calculated_score(data['customer_id'], result)
            
        except Exception as e:
            print(f"[ERROR] การคำนวณคะแนนล้มเหลว: {e}")
            
    return data

def _save_calculated_score(customer_id, result):
    """บันทึกผลการคำนวณลงฐานข้อมูล (ใช้ท่า Upsert เพื่อความชัวร์)"""
    engine = get_pg_engine()
    if not engine: 
        print("❌ ไม่สามารถเชื่อมต่อ Database Engine ได้")
        return
    
    # 1. เตรียมค่าที่จะบันทึก (คำนวณจาก result ที่ส่งมาจาก scoring_logic)
    score = result.get('credit_score', 0)
    rating = result.get('credit_rating', 'N/A')
    
    # กำหนด Risk Category ตามคะแนน
    if score >= 750:
        risk_cat = 'Low Risk'
    elif score >= 650:
        risk_cat = 'Medium Risk'
    else:
        risk_cat = 'High Risk'
        
    score_range = "300-900" # ช่วงคะแนนมาตรฐาน

    try:
        with engine.begin() as conn:
            # 2. ใช้ SQL แบบ ON CONFLICT เพื่อให้ระบบบันทึกทับคนเดิมได้
            save_sql = text("""
                INSERT INTO credit_scoring.credit_scores 
                (customer_id, credit_score, credit_rating, score_range, risk_category, last_update_date)
                VALUES (:cid, :score, :rating, :s_range, :risk, NOW())
                ON CONFLICT (customer_id) 
                DO UPDATE SET 
                    credit_score = EXCLUDED.credit_score,
                    credit_rating = EXCLUDED.credit_rating,
                    score_range = EXCLUDED.score_range,
                    risk_category = EXCLUDED.risk_category,
                    last_update_date = NOW();
            """)
            
            conn.execute(save_sql, {
                "cid": customer_id, 
                "score": score, 
                "rating": rating,
                "s_range": score_range,
                "risk": risk_cat
            })
            print(f"✅ บันทึกข้อมูลสำเร็จ: {customer_id} | Score: {score} | Risk: {risk_cat}")
            
    except Exception as e:
        # ถ้ายังไม่ได้อีก ตัวนี้จะบอกว่าติดที่คอลัมน์ไหน
        print(f"❌ เกิดข้อผิดพลาดตอนบันทึก: {str(e)}")

# ==================================================
# ส่วนจัดการหน้า Overview Dashboard
# ==================================================

def load_data() -> pd.DataFrame:
    engine = get_pg_engine()
    if engine is None: return pd.DataFrame()

    try:
        query = """
        SELECT 
            m.*, c.career_name, b.branch_no, g.gender_name, p.province_name
        FROM members m
        LEFT JOIN careers c   ON m.career_id = c.career_id
        LEFT JOIN branches b  ON m.branch_id = b.branch_id
        LEFT JOIN gender g    ON m.gender_id = g.gender_id
        LEFT JOIN addresses a ON m.member_id = a.member_id  
        LEFT JOIN provinces p ON a.province_id = p.province_id
        """
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
    except SQLAlchemyError as e:
        print(f"[ERROR] load_data: {e}")
        return pd.DataFrame()

    if df.empty: return df

    if "birthday" in df.columns:
        df["Age"] = df["birthday"].apply(calculate_age_from_dob)
        df["Age_Group"] = pd.cut(df["Age"], bins=[0, 20, 30, 40, 50, 60, 120],
                                 labels=["<20", "20-29", "30-39", "40-49", "50-59", "60+"])

    # สร้างคอลัมน์หลอกเพื่อป้องกัน Error ในหน้า Dashboard หาก DB ยังไม่มี
    for col in ['credit_limit', 'credit_limit_used_pct', 'yearly_debt_payments']:
        if col not in df.columns:
            df[col] = 0

    return df

def test_connection() -> bool:
    engine = get_pg_engine()
    if engine is None: return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except:
        return False

if __name__ == "__main__":
    print(f"Database Connection: {test_connection()}")
import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
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

import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
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
    """ดึงข้อมูลดิบจากหลายตารางมาประกอบกันเพื่อแสดงผลและคำนวณ"""
    engine = get_pg_engine()
    if engine is None: return None
    try:
        with engine.connect() as conn:
            # 1. ดึงข้อมูลส่วนบุคคลและคะแนน (LEFT JOIN เพื่อให้ดึงคนไม่มีคะแนนออกมาได้)
            cust_query = text("""
                SELECT c.*, sc.credit_score, sc.credit_rating, sc.risk_category, sc.score_range
                FROM credit_scoring.customers c
                LEFT JOIN credit_scoring.credit_scores sc ON c.customer_id = sc.customer_id
                WHERE c.national_id = :nid 
                LIMIT 1
            """)
            df_cust = pd.read_sql(cust_query, conn, params={"nid": str(national_id).strip()})
            
            if df_cust.empty: 
                print(f"[DEBUG] ไม่พบ National ID: {national_id} ในตาราง customers")
                return None
            
            res_data = df_cust.iloc[0].to_dict()
            customer_id = res_data['customer_id']

            # 2. ดึงข้อมูลบัญชีสินเชื่อ + ประวัติการชำระ (แก้ไขจุด JOIN h.customer_id ตามโครงสร้างจริง)
            # ดึงฟิลด์ monthly_payment และ account_status มาด้วยเพื่อให้ UI แสดงครบ
            acc_query = text("""
                SELECT a.*, 
                       h.payment_performance_pct, h.installments_overdue, h.days_past_due,
                       h.late_payment_count_12m, h.late_payment_count_24m, h.overdue_amount,
                       s.credit_utilization_rate, s.total_accounts
                FROM credit_scoring.credit_accounts a
                LEFT JOIN credit_scoring.payment_history h ON a.customer_id = h.customer_id
                LEFT JOIN credit_scoring.credit_summary s ON a.customer_id = s.customer_id
                WHERE a.customer_id = :cid
            """)
            df_acc = pd.read_sql(acc_query, conn, params={"cid": customer_id})
            
            # ลบข้อมูลบัญชีที่อาจซ้ำซ้อน
            df_acc = df_acc.drop_duplicates(subset=['account_number'])
            
            accounts_list = df_acc.fillna("-").to_dict('records')
            
            # 3. ประกอบข้อมูล (ส่งค่า '-' กลับไปแทนค่าว่างเพื่อให้ UI ไม่ Error)
            result = {k: (v if pd.notna(v) and v is not None else "-") for k, v in res_data.items()}
            result['accounts'] = accounts_list
            
            # ดึงข้อมูลบัญชีแรกมาไว้ที่ Root เพื่อความเข้ากันได้กับ Logic เดิม (ถ้ามี)
            if accounts_list:
                result.update(accounts_list[0])

            return result
            
    except Exception as e:
        print(f"[ERROR] get_full_member_data: {e}")
        return None

def get_member_profile(national_id: str):
    """ฟังก์ชันที่หน้า UI เรียกใช้: จัดการคำนวณและบันทึกอัตโนมัติหากยังไม่มีคะแนน"""
    data = get_full_member_data(national_id)
    if not data: return None

    # เช็คว่ามีคะแนนหรือยัง (ตรวจสอบค่า "-" หรือ None)
    current_score = data.get('credit_score')
    
    if current_score == "-" or current_score is None:
        print(f"🔄 กำลังคำนวณคะแนนอัตโนมัติสำหรับ ID: {data['customer_id']}")
        try:
            calculator = CreditScoreCalculator()
            
            # เตรียม Input โดยการดึงข้อมูลบัญชีมาเป็นตัวตั้งต้นคำนวณ
            calc_input = data.copy()
            
            # ทำความสะอาดข้อมูล (เปลี่ยน '-' เป็นค่าตัวเลขก่อนส่งเข้าสูตรคำนวณ)
            for k, v in calc_input.items():
                if v == "-":
                    if any(x in k for x in ['pct', 'rate']): 
                        calc_input[k] = 100.0
                    else: 
                        calc_input[k] = 0

            # 🚀 สั่งคำนวณผ่าน Calculator
            result = calculator.calculate_all(calc_input)
            
            # วิเคราะห์ Risk Category ตามผลลัพธ์
            score_val = result.get('credit_score', 0)
            rating_val = result.get('credit_rating', 'FF')
            risk_cat = 'ความเสี่ยงต่ำ' if score_val >= 750 else ('เสี่ยงปานกลาง' if score_val >= 650 else 'ความเสี่ยงสูง')
            
            # อัปเดตข้อมูลที่จะแสดงบนหน้าจอทันที
            data.update({
                'credit_score': score_val,
                'credit_rating': rating_val,
                'risk_category': risk_cat,
                'score_range': _get_range(rating_val)
            })
            
            # 💾 บันทึกลง Database (ตาราง credit_scores) ทันที
            _save_calculated_score(data['customer_id'], score_val, rating_val, risk_cat)
            
        except Exception as e:
            print(f"[ERROR] คำนวณอัตโนมัติล้มเหลว: {e}")
            
    return data

def _get_range(rating):
    """แผนผังช่วงคะแนนตามเรตติ้ง"""
    return {
        'AA': '753-900', 
        'BB': '725-752', 
        'CC': '616-724', 
        'HH': '300-615'
    }.get(rating, '300-900')

def _save_calculated_score(customer_id, score, rating, risk):
    """ฟังก์ชันสำหรับ Upsert ข้อมูลคะแนนลงฐานข้อมูล"""
    engine = get_pg_engine()
    if not engine: return
    try:
        with engine.begin() as conn:
            save_sql = text("""
                INSERT INTO credit_scoring.credit_scores 
                (customer_id, credit_score, credit_rating, score_range, risk_category, last_update_date)
                VALUES (:cid, :score, :rating, :range, :risk, NOW())
                ON CONFLICT (customer_id) DO UPDATE SET 
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
                "range": _get_range(rating), 
                "risk": risk
            })
            print(f"✅ บันทึกคะแนนใหม่สำเร็จสำหรับ ID: {customer_id}")
    except Exception as e:
        print(f"❌ บันทึกคะแนนล้มเหลว: {e}")
    

def load_data() -> pd.DataFrame:
    engine = get_pg_engine()
    if engine is None: return pd.DataFrame()

    try:
        query = """
        SELECT 
            m.*, 
            a.net_yearly_income,
            a.yearly_debt_payments,
            a.credit_limit,
            a.credit_limit_used_pct,
            -- คำนวณสถานะหนี้เสียเบื้องต้น (เช่น ใช้เกิน 95% ของวงเงิน)
            CASE WHEN a.credit_limit_used_pct > 95 THEN 1 ELSE 0 END as is_npl,
            c.career_name, 
            b.branch_no, 
            g.gender_name, 
            p.province_name,
            a_addr.district as district_name,
            a_addr.subdistrict as subdistrict_name,
            a_addr.moo as village_moo
        FROM (
            SELECT *, ROW_NUMBER() OVER (ORDER BY member_id) AS rn FROM members
        ) m
        INNER JOIN (
            SELECT *, ROW_NUMBER() OVER (ORDER BY amount_id) AS rn FROM amount
        ) a ON m.rn = a.rn
        LEFT JOIN careers c   ON m.career_id = c.career_id
        LEFT JOIN branches b  ON m.branch_id = b.branch_id
        LEFT JOIN gender g    ON m.gender_id = g.gender_id
        LEFT JOIN addresses a_addr ON m.member_id = a_addr.member_id
        LEFT JOIN provinces p ON a_addr.province_id = p.province_id
        """
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
    except SQLAlchemyError as e:
        print(f"[ERROR] load_data: {e}")
        return pd.DataFrame()

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
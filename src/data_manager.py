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
                    c.*,  -- ข้อมูลส่วนบุคคล (ชื่อ, อายุ, เพศ, การศึกษา, อาชีพ, รายได้ ฯลฯ)
                    a.*,  -- รายละเอียดสินเชื่อ (เลขบัญชี, ประเภทสินเชื่อ, ยอดหนี้, สถานะบัญชี)
                    h.*,  -- ประวัติการชำระ (Payment Performance, งวดค้างชำระ)
                    s.*,  -- พฤติกรรมเครดิต (Credit Utilization, จำนวนบัญชีทั้งหมด)
                    sc.credit_score, sc.credit_rating, sc.risk_category, sc.score_range
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
    data = get_full_member_data(national_id)
    if not data: return None

    # 1. เช็คว่ามีคะแนนอยู่แล้วใน DB หรือไม่
    # ระวัง: get_full_member_data คืนค่าเป็น "-" ถ้าว่าง
    current_score = data.get('credit_score')
    
    if current_score == "-" or current_score is None:
        try:
            calculator = CreditScoreCalculator()
            
            # 2. สร้าง Dictionary ใหม่สำหรับคำนวณโดยเฉพาะ (ห้ามใช้ค่าที่เป็น String "-")
            calc_input = {}
            for k, v in data.items():
                if v == "-":
                    # เติมค่า Default ที่เป็นกลางที่สุด (หรือไม่ส่งไปเลยเพื่อให้ Logic ใช้ Default ของมันเอง)
                    if k == 'payment_performance_pct': calc_input[k] = 100.0
                    elif k in ['credit_utilization_rate']: calc_input[k] = 0.0
                    else: calc_input[k] = 0
                else:
                    # พยายามแปลงเป็นตัวเลขถ้าทำได้
                    try:
                        calc_input[k] = float(v) if not isinstance(v, str) else v
                    except:
                        calc_input[k] = v
            
            # 🚀 ลอง Print ดูที่นี่ว่าค่าที่ส่งไปคำนวณของกลุ่ม GG เป็น 0 หรือ 100 หมดไหม
            # print(f"DEBUG INPUT FOR {data['customer_id']}: {calc_input}")

            result = calculator.calculate_all(calc_input)
            
            # อัปเดตข้อมูลที่จะส่งคืนให้ UI
            data.update({
                'credit_score': result.get('credit_score'),
                'credit_rating': result.get('credit_rating'),
                'score_breakdown': result.get('breakdown', {})
            })
            
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
    
    # 1. เตรียมค่าที่จะบันทึก
    score = result.get('credit_score', 0)
    rating = result.get('credit_rating', 'N/A')
    
    # --- 🟢 จุดที่ต้องเพิ่มกลับเข้าไป: กำหนด Risk Category ตามคะแนน ---
    if score >= 750:
        risk_cat = 'ความเสี่ยงต่ำ'
    elif score >= 650:
        risk_cat = 'ความเสี่ยงปานกลาง'
    else:
        risk_cat = 'ความเสี่ยงสูง'
    # -------------------------------------------------------

    # กำหนดช่วงคะแนนตาม Rating (แก้ไขปัญหา 300-900 ที่เจอใน DBeaver)
    range_map = {
        'AA': '753-900',
        'BB': '725-752',
        'CC': '616-724',
        'HH': '300-615',
        'FF': '300-900' 
    }
    score_range = range_map.get(rating, "300-900")

    try:
        with engine.begin() as conn:
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
                "risk": risk_cat # ตอนนี้ risk_cat มีค่าแล้ว จะไม่ Error
            })
            print(f"✅ บันทึกข้อมูลสำเร็จ: {customer_id} | Score: {score} | Risk: {risk_cat}")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดตอนบันทึก: {str(e)}")



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
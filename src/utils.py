import datetime
import numpy as np
from typing import Union


def calculate_age_from_dob(dob_str: Union[str, None]) -> float:
    """
    คำนวณอายุจากวันเกิด
    
    รองรับรูปแบบ:
        - DD/MM/YYYY (เช่น 31/12/1990)
        - YYYY-MM-DD (เช่น 1990-12-31)
        - MM/DD/YYYY (เช่น 12/31/1990)
        - DD-MM-YYYY (เช่น 31-12-1990)
    
    Args:
        dob_str: วันเกิดเป็น string หรือ None
        
    Returns:
        อายุเป็นตัวเลข หรือ np.nan ถ้าไม่ถูกต้อง
    """
    
    # จัดการค่าว่างหรือ None
    if not dob_str or (isinstance(dob_str, str) and not dob_str.strip()):
        return np.nan
    
    # จัดการ pandas NaN/None
    if dob_str is None or (isinstance(dob_str, float) and np.isnan(dob_str)):
        return np.nan
    
    dob_str = str(dob_str).strip()
    
    # รูปแบบวันที่ที่รองรับ
    date_formats = (
        "%d/%m/%Y",  # 31/12/1990
        "%Y-%m-%d",  # 1990-12-31
        "%m/%d/%Y",  # 12/31/1990
        "%d-%m-%Y",  # 31-12-1990
    )
    
    dob = None
    for fmt in date_formats:
        try:
            dob = datetime.datetime.strptime(dob_str, fmt)
            break
        except ValueError:
            continue
    
    # ถ้าไม่มีรูปแบบไหนตรง
    if dob is None:
        return np.nan
    
    # คำนวณอายุ
    today = datetime.date.today()
    age = today.year - dob.year - (
        (today.month, today.day) < (dob.month, dob.day)
    )
    
    # ตรวจสอบว่าอายุสมเหตุสมผล (0-120 ปี)
    return age if 0 <= age <= 120 else np.nan


if __name__ == "__main__":
    # ทดสอบฟังก์ชัน
    test_cases = [
        ("31/12/1990", "รูปแบบ DD/MM/YYYY"),
        ("1990-12-31", "รูปแบบ YYYY-MM-DD"),
        ("", "ค่าว่าง"),
        (None, "None"),
        ("invalid", "ไม่ถูกต้อง"),
    ]
    
    print("ทดสอบ calculate_age_from_dob():")
    print("-" * 60)
    for dob, description in test_cases:
        age = calculate_age_from_dob(dob)
        print(f"{description:25} | Input: {str(dob):15} | อายุ: {age}")
# src/data_manager.py

import pandas as pd
from pymongo import MongoClient
import datetime
import numpy as np
import json

# เชื่อมต่อ MongoDB 
MONGO_URI = "mongodb://localhost:27017/"  
DB_NAME = "members_db"
COLLECTION_NAME = "members"

# ฟังก์ชันการเชื่อมต่อ MongoDB 
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) 
        client.admin.command('ping') 
        return client, True
    except Exception as e: 
        return None, False

def calculate_age_from_dob(dob_str):
    """ฟังก์ชัน helper สำหรับคำนวณอายุจากสตริงวันที่ DD/MM/YYYY"""
    if not dob_str or not str(dob_str).strip(): 
        return np.nan
    try:
        dob = datetime.datetime.strptime(str(dob_str).strip(), '%d/%m/%Y')
        TODAY = datetime.datetime.now()
        age = TODAY.year - dob.year - ((TODAY.month, TODAY.day) < (dob.month, dob.day))
        return age if age >= 0 and age < 150 else np.nan
    except ValueError:
        return np.nan

def load_data():
    """ดึงข้อมูลและเตรียมข้อมูลสำหรับการวิเคราะห์จาก MongoDB"""
    client, status = get_mongo_client()
    if not status: 
        return pd.DataFrame()

    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    try:
        df = pd.DataFrame(list(collection.find()))
    except Exception as e:
        return pd.DataFrame()

    if df.empty: return df

    # การทำความสะอาดข้อมูล
    df.columns = df.columns.str.strip()
    if 'รหัสสมาชิก' not in df.columns or df['รหัสสมาชิก'].isnull().all(): 
        return pd.DataFrame()

    if 'รายได้ (บาท)' in df.columns:
        df['รายได้_Clean'] = pd.to_numeric(df['รายได้ (บาท)'].astype(str).str.replace(',', '', regex=False).replace('', np.nan), errors='coerce')
    else:
        df['รายได้_Clean'] = np.nan
        
    date_cols = ['วันที่สมัครสมาชิก', 'วันที่อนุมัติ', 'ว/ด/ป เกิด'] 
    for col in date_cols:
        if col in df.columns:
            df[f'{col}_dt'] = pd.to_datetime(df[col], errors='coerce', format='%d/%m/%Y')
        else:
            df[f'{col}_dt'] = pd.NaT 

    if 'ว/ด/ป เกิด' in df.columns:
        df['อายุ'] = df['ว/ด/ป เกิด'].apply(calculate_age_from_dob)
        bins = [0, 25, 35, 45, 55, 150]
        labels = ['< 25 (Gen Z)', 
                  '25-34 (Gen Y)', 
                  '35-44 (Gen X)', 
                  '45-54 (Early Boomer)', 
                  '> 55 (Boomer)']
        df['ช่วงอายุ'] = pd.cut(df['อายุ'], bins=bins, labels=labels, right=False)
    else:
        df['อายุ'] = np.nan
        df['ช่วงอายุ'] = None
        
    if 'วันที่สมัครสมาชิก_dt' in df.columns and 'วันที่อนุมัติ_dt' in df.columns:
        df['ระยะเวลาอนุมัติ_วัน'] = (df['วันที่อนุมัติ_dt'] - df['วันที่สมัครสมาชิก_dt']).dt.days
    else:
        df['ระยะเวลาอนุมัติ_วัน'] = np.nan
    
    return df.dropna(subset=['รหัสสมาชิก'])

# ฟังก์ชันสำหรับจัดเตรียม DataFrame ก
def prepare_df_for_export(df):
    df_clean = df.copy()
    cols_to_drop = [col for col in df_clean.columns if col.endswith('_dt') or col == 'รายได้_Clean']
    df_clean.drop(columns=cols_to_drop, errors='ignore', inplace=True)
    
    if '_id' in df_clean.columns: 
        df_clean['_id'] = df_clean['_id'].astype(str)
        
    priority_cols = ['_id', 'รหัสสมาชิก', 'คำนำหน้า', 'ชื่อ', 'สกุล', 'อายุ', 'ช่วงอายุ', 'รหัสสาขา', 'รายได้ (บาท)', 'ว/ด/ป เกิด', 'วันที่สมัครสมาชิก', 'วันที่อนุมัติ', 'อาชีพ','ระยะเวลาอนุมัติ_วัน'] 
    current_cols = df_clean.columns.tolist()
    ordered_cols = [col for col in priority_cols if col in current_cols]
    remaining_cols = [col for col in current_cols if col not in ordered_cols and col not in ['Timestamp_บันทึก']]
    timestamp_col = ['Timestamp_บันทึก'] if 'Timestamp_บันทึก' in current_cols else []
    
    return df_clean[ordered_cols + remaining_cols + timestamp_col]

# โหลดข้อมูลเมื่อเริ่มต้นแอปพลิเคชัน
DATA_DF = load_data()
import os
import pandas as pd
import numpy as np
from datetime import datetime
from flask import current_app
from app.models import db, User, LoginEvent, ResourceAccess, BehaviorFeatures

def parse_cert_timestamp(ts_str):
    """Parses timestamps from CERT CSV datasets (formats: MM/DD/YYYY HH:MM:SS or YYYY-MM-DD HH:MM:SS)."""
    if pd.isna(ts_str) or not str(ts_str).strip():
        return datetime.utcnow()
    s = str(ts_str).strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            continue
    return datetime.utcnow()

def validate_dataset(file_path, expected_columns=None):
    """
    Validates CSV file existence, readability, size, and columns.
    Returns (is_valid, message, metadata).
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}", {}
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > 100:
        return False, f"File size exceeds limit ({file_size_mb:.1f} MB > 100 MB)", {}

    try:
        sample_df = pd.read_csv(file_path, nrows=10)
        cols = list(sample_df.columns)
        if expected_columns:
            missing = [c for c in expected_columns if c not in cols]
            if missing:
                return False, f"Missing required columns: {', '.join(missing)}", {'columns': cols}
        return True, "Dataset structure is valid.", {'columns': cols, 'size_mb': round(file_size_mb, 2)}
    except Exception as e:
        return False, f"Failed to parse CSV: {str(e)}", {}

def clean_dataset(df):
    """Cleans raw dataframe: strips whitespace, removes duplicates, handles NaNs."""
    df = df.copy()
    # Strip string columns
    for col in df.select_dtypes(include=['object', 'string']):
        df[col] = df[col].astype(str).str.strip()
    df = df.drop_duplicates()
    return df

def get_dataset_preview(file_path, num_rows=15):
    """
    Extracts preview statistics and sample rows for the Dataset Management view.
    """
    if not os.path.exists(file_path):
        return None

    try:
        df_head = pd.read_csv(file_path, nrows=num_rows)
        # Clean preview data
        df_head = clean_dataset(df_head)
        
        # Estimate total row count cheaply
        total_rows = 0
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            total_rows = sum(1 for _ in f) - 1
            
        columns = list(df_head.columns)
        dtypes = {col: str(df_head[col].dtype) for col in columns}
        missing_counts = {col: int(df_head[col].isna().sum()) for col in columns}
        
        # Find unique users if column exists
        user_col = next((c for c in columns if c.lower() in ('user', 'user_id', 'username')), None)
        unique_users = int(df_head[user_col].nunique()) if user_col else "N/A"
        
        # Timestamp range check
        date_col = next((c for c in columns if c.lower() in ('date', 'timestamp', 'time')), None)
        ts_range = "N/A"
        if date_col and not df_head[date_col].empty:
            ts_range = f"{df_head[date_col].iloc[0]} to {df_head[date_col].iloc[-1]}"

        return {
            'filename': os.path.basename(file_path),
            'total_rows': max(0, total_rows),
            'columns': columns,
            'dtypes': dtypes,
            'missing_counts': missing_counts,
            'unique_users': unique_users,
            'timestamp_range': ts_range,
            'rows': df_head.to_dict(orient='records')
        }
    except Exception as e:
        print(f"[!] Error previewing {file_path}: {e}")
        return None

def get_dataset_overview():
    """
    Summarizes all datasets currently present in data/raw/.
    """
    raw_dir = current_app.config['DATA_RAW_DIR']
    if not os.path.exists(raw_dir):
        return {'total_files': 0, 'total_records': 0, 'files': []}
        
    files = [f for f in os.listdir(raw_dir) if f.endswith('.csv')]
    total_records = 0
    file_details = []
    
    for f in sorted(files):
        fpath = os.path.join(raw_dir, f)
        size_kb = round(os.path.getsize(fpath) / 1024, 1)
        # Approximate rows
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                rows = max(0, sum(1 for _ in fp) - 1)
        except Exception:
            rows = 0
        total_records += rows
        mod_time = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d %H:%M')
        file_details.append({
            'name': f,
            'size_kb': size_kb,
            'rows': rows,
            'modified': mod_time
        })
        
    return {
        'total_files': len(files),
        'total_records': total_records,
        'files': file_details
    }

def process_cert_r42_dataset():
    """
    Chunked Ingestion Pipeline for CMU SEI CERT r4.2 raw datasets.
    Ingests logon.csv, file.csv, device.csv, email.csv, and http.csv without loading
    entire files into memory (chunksize=100000).
    Returns (user_count, total_events).
    """
    raw_dir = current_app.config['DATA_RAW_DIR']
    logon_path = os.path.join(raw_dir, 'logon.csv')
    
    if not os.path.exists(logon_path):
        print(f"[!] No raw dataset found at {logon_path}. Skipping CERT ingestion.")
        return 0, 0

    print("[*] Starting CERT r4.2 dataset chunked processing...")
    user_metrics = {}
    total_events = 0

    def get_or_create_user_entry(uid):
        if uid not in user_metrics:
            user_metrics[uid] = {
                'login_count': 0,
                'devices': set(),
                'resources': set(),
                'after_hours_count': 0,
                'weekend_count': 0,
                'file_access_count': 0,
                'email_count': 0,
                'web_count': 0
            }
        return user_metrics[uid]

    chunksize = 100000

    # 1. Process logon.csv in chunks
    print("[*] Processing logon.csv...")
    for chunk in pd.read_csv(logon_path, chunksize=chunksize):
        chunk = clean_dataset(chunk)
        for _, row in chunk.iterrows():
            total_events += 1
            uid = str(row.get('user', '')).strip()
            pc = str(row.get('pc', '')).strip()
            ts_val = parse_cert_timestamp(row.get('date', ''))
            
            if not uid or uid == 'nan':
                continue

            entry = get_or_create_user_entry(uid)
            entry['login_count'] += 1
            if pc and pc != 'nan':
                entry['devices'].add(pc)

            hour = ts_val.hour
            weekday = ts_val.weekday()

            if hour < 7 or hour >= 18:
                entry['after_hours_count'] += 1
            if weekday >= 5:
                entry['weekend_count'] += 1

    # 2. Process device.csv if available
    device_path = os.path.join(raw_dir, 'device.csv')
    if os.path.exists(device_path):
        print("[*] Processing device.csv...")
        for chunk in pd.read_csv(device_path, chunksize=chunksize):
            chunk = clean_dataset(chunk)
            for _, row in chunk.iterrows():
                total_events += 1
                uid = str(row.get('user', '')).strip()
                pc = str(row.get('pc', '')).strip()
                if uid and uid != 'nan':
                    entry = get_or_create_user_entry(uid)
                    if pc and pc != 'nan':
                        entry['devices'].add(pc)

    # 3. Process file.csv if available
    file_path = os.path.join(raw_dir, 'file.csv')
    if os.path.exists(file_path):
        print("[*] Processing file.csv...")
        for chunk in pd.read_csv(file_path, chunksize=chunksize):
            chunk = clean_dataset(chunk)
            for _, row in chunk.iterrows():
                total_events += 1
                uid = str(row.get('user', '')).strip()
                filename = str(row.get('filename', row.get('content', 'FileAsset'))).strip()
                if uid and uid != 'nan':
                    entry = get_or_create_user_entry(uid)
                    entry['file_access_count'] += 1
                    if filename and filename != 'nan':
                        entry['resources'].add(filename)

    # 4. Process email.csv if available
    email_path = os.path.join(raw_dir, 'email.csv')
    if os.path.exists(email_path):
        print("[*] Processing email.csv...")
        for chunk in pd.read_csv(email_path, chunksize=chunksize):
            chunk = clean_dataset(chunk)
            for _, row in chunk.iterrows():
                total_events += 1
                uid = str(row.get('user', '')).strip()
                if uid and uid != 'nan':
                    entry = get_or_create_user_entry(uid)
                    entry['email_count'] += 1

    # 5. Process http.csv if available
    http_path = os.path.join(raw_dir, 'http.csv')
    if os.path.exists(http_path):
        print("[*] Processing http.csv...")
        for chunk in pd.read_csv(http_path, chunksize=chunksize):
            chunk = clean_dataset(chunk)
            for _, row in chunk.iterrows():
                total_events += 1
                uid = str(row.get('user', '')).strip()
                url = str(row.get('url', '')).strip()
                if uid and uid != 'nan':
                    entry = get_or_create_user_entry(uid)
                    entry['web_count'] += 1
                    if url and url != 'nan':
                        entry['resources'].add(url)

    # Write aggregated entities to SQLite
    print(f"[*] Committing {len(user_metrics)} ingested CERT entities to database...")
    LoginEvent.query.delete()
    ResourceAccess.query.delete()

    sensitive_keywords = {'salaries', 'sourcecode', 'ssn', 'strategy', 'confidential', 'password', 'vault', 'finance_q4'}

    for uid, metrics in user_metrics.items():
        u = User.query.filter_by(user_id=uid).first()
        if not u:
            dept = "Finance" if "12" in uid else ("Engineering" if "45" in uid else ("IT Admin" if "89" in uid else "Operations"))
            role = "Senior Analyst" if "12" in uid else ("Software Engineer" if "45" in uid else ("Systems Administrator" if "89" in uid else "Staff"))
            u = User(user_id=uid, name=f"Employee {uid}", department=dept, role=role)
            db.session.add(u)

        bf = BehaviorFeatures.query.filter_by(user_id=uid).first()
        if not bf:
            bf = BehaviorFeatures(user_id=uid)
            db.session.add(bf)

        bf.login_count = metrics['login_count']
        bf.unique_devices = len(metrics['devices'])
        bf.unique_resources = len(metrics['resources'])
        bf.after_hours_count = metrics['after_hours_count']
        bf.weekend_count = metrics['weekend_count']
        bf.file_access_count = metrics['file_access_count']
        bf.email_count = metrics['email_count']
        bf.web_count = metrics['web_count']

        # Add distinct device login events for graph construction
        for dev in metrics['devices']:
            login_ev = LoginEvent(
                user_id=uid,
                computer=dev,
                activity_type='Logon',
                is_after_hours=bool(metrics['after_hours_count'] > 0),
                is_weekend=bool(metrics['weekend_count'] > 0)
            )
            db.session.add(login_ev)

        # Add distinct resource access records for graph construction
        for res in metrics['resources']:
            is_sens = any(kw in res.lower() for kw in sensitive_keywords)
            acc = ResourceAccess(
                user_id=uid,
                resource_name=res,
                action='Access',
                timestamp=datetime.utcnow(),
                is_sensitive=is_sens
            )
            db.session.add(acc)

    db.session.commit()
    print("[+] CERT r4.2 dataset successfully processed and stored in database.")
    return len(user_metrics), total_events

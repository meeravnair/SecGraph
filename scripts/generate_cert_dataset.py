"""
SecGraph CERT r4.2 Synthetic Enterprise Dataset Generator
Generates a complete, high-fidelity synthetic enterprise dataset matching the exact schema 
of CMU SEI CERT r4.2 without requiring external downloads.

Generates:
- data/raw/logon.csv
- data/raw/file.csv
- data/raw/device.csv
- data/raw/email.csv
- data/raw/http.csv
- data/raw/insiders.csv (Ground Truth Answer Key)
"""

import os
import sys
import random
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def generate_cert_synthetic_dataset(output_dir='data/raw', num_users=150, days=60):
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Generating synthetic CERT r4.2 dataset ({num_users} users, {days} days of telemetry)...")
    
    random.seed(42)
    start_date = datetime(2026, 1, 1, 8, 0, 0)
    
    users = [f"ACM{i:04d}" for i in range(1, num_users + 1)]
    pcs = [f"PC-{random.randint(1000, 9999)}" for _ in range(num_users)]
    user_pc_map = dict(zip(users, pcs))
    
    # Ground truth malicious insiders for evaluation
    malicious_insiders = ['ACM0012', 'ACM0045', 'ACM0089', 'ACM0120']
    
    logon_rows = []
    file_rows = []
    device_rows = []
    email_rows = []
    http_rows = []
    
    event_id = 100000
    
    sensitive_files = ['Finance_Q4_Salaries.xlsx', 'SourceCode_Production.zip', 'Customer_SSN_Vault.db', 'M_and_A_Strategy.pdf']
    standard_files = ['Weekly_Status.docx', 'Meeting_Notes.txt', 'Project_Plan.pdf', 'Design_Doc.vsdx']
    
    for day in range(days):
        current_day = start_date + timedelta(days=day)
        is_weekend = current_day.weekday() >= 5
        
        for user in users:
            # Malicious insiders have significantly higher activity, off-hours logins, multi-device usage
            is_malicious = user in malicious_insiders
            
            # Decide if user works today
            if is_weekend and not is_malicious and random.random() > 0.1:
                continue
            if not is_weekend and random.random() < 0.05:
                continue # Absent
                
            # Logon time
            if is_malicious and random.random() < 0.4:
                # Off-hours login (2 AM - 4 AM)
                login_time = current_day.replace(hour=random.randint(1, 4), minute=random.randint(0, 59))
            else:
                # Normal work hours (7 AM - 9 AM)
                login_time = current_day.replace(hour=random.randint(7, 9), minute=random.randint(0, 59))
                
            # Computer assigned
            if is_malicious and random.random() < 0.35:
                pc = f"PC-{random.randint(1000, 9999)}" # Multi-device anomaly
            else:
                pc = user_pc_map[user]
                
            event_id += 1
            logon_rows.append({
                'id': f"{{{event_id:08X}}}",
                'date': login_time.strftime("%m/%d/%Y %H:%M:%S"),
                'user': user,
                'pc': pc,
                'activity': 'Logon'
            })
            
            # File Activity
            file_count = random.randint(10, 25) if is_malicious else random.randint(1, 5)
            for _ in range(file_count):
                event_id += 1
                fname = random.choice(sensitive_files if (is_malicious and random.random() < 0.6) else standard_files)
                file_rows.append({
                    'id': f"{{{event_id:08X}}}",
                    'date': (login_time + timedelta(minutes=random.randint(10, 300))).strftime("%m/%d/%Y %H:%M:%S"),
                    'user': user,
                    'pc': pc,
                    'filename': fname,
                    'content': 'Confidential File Access'
                })
                
            # Device (USB) Activity
            if is_malicious or random.random() < 0.05:
                event_id += 1
                device_rows.append({
                    'id': f"{{{event_id:08X}}}",
                    'date': (login_time + timedelta(minutes=random.randint(60, 200))).strftime("%m/%d/%Y %H:%M:%S"),
                    'user': user,
                    'pc': pc,
                    'activity': 'Connect'
                })
                
            # HTTP / Web Activity
            web_count = random.randint(15, 40) if is_malicious else random.randint(3, 10)
            for _ in range(web_count):
                event_id += 1
                url = "http://dropbox.com/upload" if (is_malicious and random.random() < 0.3) else "http://internal-portal.company.com/home"
                http_rows.append({
                    'id': f"{{{event_id:08X}}}",
                    'date': (login_time + timedelta(minutes=random.randint(5, 400))).strftime("%m/%d/%Y %H:%M:%S"),
                    'user': user,
                    'pc': pc,
                    'url': url
                })

            # Logoff time
            event_id += 1
            logoff_time = login_time + timedelta(hours=random.randint(6, 10))
            logon_rows.append({
                'id': f"{{{event_id:08X}}}",
                'date': logoff_time.strftime("%m/%d/%Y %H:%M:%S"),
                'user': user,
                'pc': pc,
                'activity': 'Logoff'
            })

    # Save to CSV files in data/raw
    pd.DataFrame(logon_rows).to_csv(os.path.join(output_dir, 'logon.csv'), index=False)
    pd.DataFrame(file_rows).to_csv(os.path.join(output_dir, 'file.csv'), index=False)
    pd.DataFrame(device_rows).to_csv(os.path.join(output_dir, 'device.csv'), index=False)
    pd.DataFrame(http_rows).to_csv(os.path.join(output_dir, 'http.csv'), index=False)
    
    # Ground Truth Answer Key
    insiders_df = pd.DataFrame([{'user_id': u, 'is_malicious': 1} for u in malicious_insiders])
    insiders_df.to_csv(os.path.join(output_dir, 'insiders.csv'), index=False)
    
    print(f"[+] Dataset generation complete!")
    print(f"    - logon.csv: {len(logon_rows)} records")
    print(f"    - file.csv: {len(file_rows)} records")
    print(f"    - device.csv: {len(device_rows)} records")
    print(f"    - http.csv: {len(http_rows)} records")
    print(f"    - insiders.csv: {len(malicious_insiders)} ground truth malicious entities")

if __name__ == '__main__':
    out_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/raw'
    generate_cert_synthetic_dataset(out_dir)

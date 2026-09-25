import os
import glob
import pandas as pd

def inspect_cert_dataset(raw_dir='data/raw'):
    """
    Inspects downloaded CERT CSV files, headers, and column definitions without guessing.
    """
    csv_files = glob.glob(os.path.join(raw_dir, '*.csv'))
    if not csv_files:
        print(f"[!] No raw CSV files found in '{raw_dir}'. Place CERT r4.2 CSV files there.")
        return

    print("="*60)
    print("      CMU SEI CERT DATASET INSPECTOR")
    print("="*60)
    
    for fpath in csv_files:
        fname = os.path.basename(fpath)
        try:
            df_head = pd.read_csv(fpath, nrows=5)
            print(f"\n📄 File: {fname}")
            print(f"   Columns ({len(df_head.columns)}): {list(df_head.columns)}")
            print("   Sample Row 1:")
            print(f"   {df_head.iloc[0].to_dict()}")
        except Exception as e:
            print(f"[!] Error inspecting {fname}: {e}")
            
    print("="*60)

if __name__ == '__main__':
    inspect_cert_dataset()

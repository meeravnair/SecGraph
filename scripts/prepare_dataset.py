import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.data_processor import process_cert_r42_dataset

def main():
    app = create_app()
    with app.app_context():
        print("[*] Executing CERT Dataset Preparation Script...")
        process_cert_r42_dataset()

if __name__ == '__main__':
    main()

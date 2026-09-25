import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.ml_engine import train_behavioral_ml_model

def main():
    app = create_app()
    with app.app_context():
        print("[*] Training Isolation Forest Behavioral Model...")
        model, scaler = train_behavioral_ml_model()
        if model:
            print("[+] Behavioral Isolation Forest model trained and saved successfully.")
        else:
            print("[!] No behavioral feature data available for training.")

if __name__ == '__main__':
    main()

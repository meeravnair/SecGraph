import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from flask import current_app
from app.models import db, BehaviorFeatures

def train_behavioral_ml_model():
    """
    Trains an Unsupervised Isolation Forest model on aggregated user behavioral features.
    Saves the scaler and trained model using joblib.
    """
    features_list = BehaviorFeatures.query.all()
    if not features_list:
        return None, None
        
    data = []
    for f in features_list:
        data.append([
            f.login_count,
            f.unique_devices,
            f.unique_resources,
            f.after_hours_count,
            f.weekend_count,
            f.file_access_count,
            f.email_count,
            f.web_count
        ])
        
    df = pd.DataFrame(data, columns=[
        'login_count', 'unique_devices', 'unique_resources',
        'after_hours_count', 'weekend_count', 'file_access_count',
        'email_count', 'web_count'
    ])
    
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df)
    
    # Train Isolation Forest (Hyperparameters from Section 3.8: 100 trees, psi=256, alpha=0.08)
    model = IsolationForest(
        n_estimators=100,
        max_samples=256,
        contamination=0.08,
        random_state=42
    )
    model.fit(scaled_features)
    
    # Save artifacts
    model_dir = current_app.config['MODEL_DIR']
    os.makedirs(model_dir, exist_ok=True)
    
    joblib.dump(model, os.path.join(model_dir, 'isolation_forest.joblib'))
    joblib.dump(scaler, os.path.join(model_dir, 'scaler.joblib'))
    
    return model, scaler

def predict_anomaly_scores():
    """
    Loads trained Isolation Forest and produces normalized 0-100 anomaly scores for all users.
    """
    model_dir = current_app.config['MODEL_DIR']
    model_path = os.path.join(model_dir, 'isolation_forest.joblib')
    scaler_path = os.path.join(model_dir, 'scaler.joblib')
    
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        model, scaler = train_behavioral_ml_model()
    else:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
    features_list = BehaviorFeatures.query.all()
    results = {}
    
    if not model or not scaler or not features_list:
        return results

    feature_cols = [
        'login_count', 'unique_devices', 'unique_resources',
        'after_hours_count', 'weekend_count', 'file_access_count',
        'email_count', 'web_count'
    ]
    user_ids = []
    data = []
    for f in features_list:
        user_ids.append(f.user_id)
        data.append([
            f.login_count, f.unique_devices, f.unique_resources,
            f.after_hours_count, f.weekend_count, f.file_access_count,
            f.email_count, f.web_count
        ])

    df = pd.DataFrame(data, columns=feature_cols)
    scaled = scaler.transform(df)
    raw_scores = model.decision_function(scaled)

    for uid, raw in zip(user_ids, raw_scores):
        norm_score = max(0.0, min(100.0, (0.5 - raw) * 100))
        results[uid] = round(norm_score, 2)

    return results

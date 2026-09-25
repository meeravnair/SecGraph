import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secgraph-msc-key-2026-secure-hybrid-analyzer'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(INSTANCE_DIR, 'secgraph.db').replace('\\', '/')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage Paths
    DATA_RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    DATA_PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
    MODEL_DIR = os.path.join(BASE_DIR, 'app', 'models_store')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    
    # Hybrid Risk Weights (Configurable)
    WEIGHT_GRAPH = 0.35
    WEIGHT_BEHAVIOR = 0.35
    WEIGHT_RULE = 0.30
    
    # Risk Classification Thresholds
    THRESH_HIGH = 65
    THRESH_MEDIUM = 35

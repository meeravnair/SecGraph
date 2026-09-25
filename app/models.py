from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

def utc_now():
    return datetime.now(timezone.utc)

db = SQLAlchemy()
login_manager = LoginManager()

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='Active')

    # Relationships
    login_events = db.relationship('LoginEvent', backref='user', lazy=True, cascade="all, delete-orphan")
    resource_accesses = db.relationship('ResourceAccess', backref='user', lazy=True, cascade="all, delete-orphan")
    risk_results = db.relationship('RiskResult', backref='user', lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship('Alert', backref='user', lazy=True, cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class LoginEvent(db.Model):
    __tablename__ = 'login_events'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=utc_now)
    computer = db.Column(db.String(50), nullable=False)
    activity_type = db.Column(db.String(20), nullable=False) # Logon, Logoff
    is_after_hours = db.Column(db.Boolean, default=False)
    is_weekend = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class ResourceAccess(db.Model):
    __tablename__ = 'resource_access'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    resource_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    is_sensitive = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class BehaviorFeatures(db.Model):
    __tablename__ = 'behavior_features'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), unique=True, nullable=False)
    login_count = db.Column(db.Integer, default=0)
    unique_devices = db.Column(db.Integer, default=0)
    unique_resources = db.Column(db.Integer, default=0)
    after_hours_count = db.Column(db.Integer, default=0)
    weekend_count = db.Column(db.Integer, default=0)
    file_access_count = db.Column(db.Integer, default=0)
    email_count = db.Column(db.Integer, default=0)
    web_count = db.Column(db.Integer, default=0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class GraphMetrics(db.Model):
    __tablename__ = 'graph_metrics'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), unique=True, nullable=False)
    degree_centrality = db.Column(db.Float, default=0.0)
    betweenness_centrality = db.Column(db.Float, default=0.0)
    resource_reachability = db.Column(db.Integer, default=0)
    shortest_sensitive_path = db.Column(db.Integer, default=-1) # -1 if no path
    graph_risk_component = db.Column(db.Float, default=0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class RiskResult(db.Model):
    __tablename__ = 'risk_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False) # HIGH, MEDIUM, LOW
    graph_score = db.Column(db.Float, nullable=False)
    behavior_score = db.Column(db.Float, nullable=False)
    rule_score = db.Column(db.Float, nullable=False)
    anomaly_score = db.Column(db.Float, nullable=False)
    reasons_json = db.Column(db.Text, nullable=False)
    recommendations_json = db.Column(db.Text, nullable=False)
    analyzed_at = db.Column(db.DateTime, default=utc_now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Alert(db.Model):
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.user_id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False) # HIGH, CRITICAL, MEDIUM
    description = db.Column(db.Text, nullable=False)
    evidence_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    status = db.Column(db.String(20), default='Open') # Open, Under Review, Resolved
    notes = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class AnalysisHistory(db.Model):
    __tablename__ = 'analysis_history'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=utc_now)
    dataset_name = db.Column(db.String(100), default='CERT r4.2')
    total_records = db.Column(db.Integer, default=0)
    users_analyzed = db.Column(db.Integer, default=0)
    high_risk_count = db.Column(db.Integer, default=0)
    medium_risk_count = db.Column(db.Integer, default=0)
    low_risk_count = db.Column(db.Integer, default=0)
    anomalies_detected = db.Column(db.Integer, default=0)
    alerts_generated = db.Column(db.Integer, default=0)
    execution_time_sec = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Complete')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    w_graph = db.Column(db.Float, default=0.35)
    w_behavior = db.Column(db.Float, default=0.35)
    w_rule = db.Column(db.Float, default=0.30)
    thresh_low = db.Column(db.Float, default=34.9)
    thresh_medium = db.Column(db.Float, default=64.9)
    thresh_high = db.Column(db.Float, default=65.0)
    updated_at = db.Column(db.DateTime, default=utc_now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def get_settings(cls):
        s = cls.query.first()
        if not s:
            s = cls(w_graph=0.35, w_behavior=0.35, w_rule=0.30, thresh_low=34.9, thresh_medium=64.9, thresh_high=65.0)
            db.session.add(s)
            db.session.commit()
        return s


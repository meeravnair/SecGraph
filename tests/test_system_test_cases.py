import os
import io
import unittest
from datetime import datetime
from app import create_app
from app.models import db, AdminUser, User, BehaviorFeatures, GraphMetrics, RiskResult, Alert, SystemSetting
from app.data_processor import validate_dataset
from app.graph_engine import build_identity_access_graph, compute_and_store_graph_metrics
from app.behavior_engine import calculate_peer_baselines
from app.ml_engine import predict_anomaly_scores
from app.risk_engine import evaluate_all_user_risks, calculate_rule_score
from app.alert_engine import generate_security_alerts
from app.report_engine import generate_pdf_security_report, generate_user_risk_report

from config import Config

class TestSystemConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class SecGraphSystemTestSuite(unittest.TestCase):
    """
    Implements the 12 Comprehensive Unit and System Test Cases (TC01 to TC12)
    defined in Table 5.1 and Table 5.2 of the SecGraph Project Report.
    """

    def setUp(self):
        self.app = create_app(TestSystemConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        SystemSetting.get_settings()

        # Seed admin user
        admin = AdminUser(username='meera')
        admin.set_password('meera123')
        db.session.add(admin)

        # Seed sample user with telemetry
        user = User(user_id='ACM0012', name='Emp ACM0012', department='Finance', role='Senior Analyst')
        db.session.add(user)

        bf = BehaviorFeatures(
            user_id='ACM0012',
            login_count=120,
            unique_devices=4,
            unique_resources=18,
            after_hours_count=26,
            weekend_count=5,
            file_access_count=45,
            email_count=10,
            web_count=80
        )
        db.session.add(bf)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    # ---------------------------------------------------------
    # Phase 1: Authentication & Access Control (TC01, TC02)
    # ---------------------------------------------------------
    def test_TC01_login_valid_credentials(self):
        """TC01: Login with valid credentials -> Dashboard opens"""
        response = self.client.post('/login', data={
            'username': 'meera',
            'password': 'meera123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SECGRAPH OPERATIONS CONSOLE', response.data)

    def test_TC02_login_invalid_credentials(self):
        """TC02: Login with invalid credentials -> Error displayed"""
        response = self.client.post('/login', data={
            'username': 'meera',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    # ---------------------------------------------------------
    # Phase 2: Data Processing & Validation (TC03, TC04)
    # ---------------------------------------------------------
    def test_TC03_dataset_upload_valid_csv(self):
        """TC03: Dataset upload valid CSV -> Dataset accepted"""
        # Log in first
        self.client.post('/login', data={'username': 'meera', 'password': 'meera123'})
        csv_content = b"id,date,user,pc,activity\n1,01/02/2026 08:30:00,ACM0012,PC-1001,Logon\n"
        data = {
            'dataset_files': (io.BytesIO(csv_content), 'test_logon.csv')
        }
        response = self.client.post('/upload_dataset', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Successfully uploaded', response.data)

    def test_TC04_dataset_upload_invalid_file(self):
        """TC04: Invalid file upload -> Upload rejected"""
        self.client.post('/login', data={'username': 'meera', 'password': 'meera123'})
        exe_content = b"MZ\x90\x00BinaryMockExecutable"
        data = {
            'dataset_files': (io.BytesIO(exe_content), 'malicious.exe')
        }
        response = self.client.post('/upload_dataset', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid file format', response.data)

    # ---------------------------------------------------------
    # Phase 3: Graph & Analytics Pipeline (TC05, TC06)
    # ---------------------------------------------------------
    def test_TC05_graph_construction(self):
        """TC05: Graph construction from processed records -> Graph created"""
        G = build_identity_access_graph()
        self.assertIsNotNone(G)
        self.assertTrue(G.has_node('USER:ACM0012'))
        self.assertEqual(G.nodes['USER:ACM0012']['type'], 'User')

    def test_TC06_graph_metrics_calculation(self):
        """TC06: Graph metrics calculation -> Metrics calculated"""
        compute_and_store_graph_metrics()
        gm = GraphMetrics.query.filter_by(user_id='ACM0012').first()
        self.assertIsNotNone(gm)
        self.assertGreaterEqual(gm.degree_centrality, 0.0)
        self.assertGreaterEqual(gm.betweenness_centrality, 0.0)
        self.assertGreaterEqual(gm.graph_risk_component, 0.0)

    # ---------------------------------------------------------
    # Phase 4: Behavioral & Machine Learning (TC07, TC08)
    # ---------------------------------------------------------
    def test_TC07_behaviour_analysis(self):
        """TC07: Behaviour analysis -> Peer baselines generated"""
        baselines = calculate_peer_baselines()
        self.assertIsInstance(baselines, dict)
        self.assertIn('after_hours_count', baselines)
        self.assertIn('unique_devices', baselines)
        self.assertIn('unique_resources', baselines)

    def test_TC08_ml_anomaly_detection(self):
        """TC08: ML anomaly detection -> Predictions generated"""
        # Add a baseline peer to allow variance for ML
        u2 = User(user_id='ACM0001', name='Emp ACM0001', department='Operations', role='Staff')
        db.session.add(u2)
        bf2 = BehaviorFeatures(user_id='ACM0001', login_count=10, unique_devices=1, unique_resources=2)
        db.session.add(bf2)
        db.session.commit()

        scores = predict_anomaly_scores()
        self.assertIsInstance(scores, dict)
        if 'ACM0012' in scores:
            self.assertGreaterEqual(scores['ACM0012'], 0.0)
            self.assertLessEqual(scores['ACM0012'], 100.0)

    # ---------------------------------------------------------
    # Phase 5: Risk Scoring & Alert Generation (TC09, TC10)
    # ---------------------------------------------------------
    def test_TC09_hybrid_risk_calculation(self):
        """TC09: Risk calculation -> Final calibrated hybrid score generated"""
        compute_and_store_graph_metrics()
        summary = evaluate_all_user_risks()
        self.assertIsInstance(summary, dict)
        self.assertGreaterEqual(summary['total_users'], 1)

        rr = RiskResult.query.filter_by(user_id='ACM0012').first()
        self.assertIsNotNone(rr)
        self.assertGreaterEqual(rr.risk_score, 0.0)
        self.assertLessEqual(rr.risk_score, 100.0)
        self.assertIn(rr.risk_level, ['LOW', 'MEDIUM', 'HIGH'])

    def test_TC10_alert_generation(self):
        """TC10: Alert generation -> Alert created for high-risk identity"""
        reasons = [
            "Excessive off-hours activity: 26 logins outside business hours",
            "Multi-device proliferation: Authenticated from 4 workstations"
        ]
        generate_security_alerts('ACM0012', 84.55, 'HIGH', reasons)
        db.session.commit()

        alert = Alert.query.filter_by(user_id='ACM0012').first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.user_id, 'ACM0012')
        self.assertEqual(alert.alert_type, 'HIGH_RISK_IDENTITY')
        self.assertIn(alert.severity, ['CRITICAL', 'HIGH'])

    # ---------------------------------------------------------
    # Phase 6: User Interface & PDF Reporting (TC11, TC12)
    # ---------------------------------------------------------
    def test_TC11_user_profile_display(self):
        """TC11: User profile inspection -> Profile rendered with risk details"""
        self.client.post('/login', data={'username': 'meera', 'password': 'meera123'})
        evaluate_all_user_risks()
        response = self.client.get('/user/ACM0012')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ACM0012', response.data)
        self.assertIn(b'Identity Risk Profile', response.data)

    def test_TC12_pdf_report_generation(self):
        """TC12: PDF report generation -> PDF successfully compiled"""
        evaluate_all_user_risks()
        os.makedirs('reports', exist_ok=True)
        pdf_path = os.path.join('reports', 'TC12_test_report.pdf')
        generated_file = generate_pdf_security_report(pdf_path)
        self.assertTrue(os.path.exists(generated_file))
        self.assertGreater(os.path.getsize(generated_file), 1000)

if __name__ == '__main__':
    unittest.main()

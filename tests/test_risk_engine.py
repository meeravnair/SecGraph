import unittest
from app import create_app
from app.models import db, User, RiskResult
from app.risk_engine import evaluate_all_user_risks

from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class TestRiskEngine(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_risk_evaluation_flow(self):
        u = User(user_id='UTEST01', name='Test User', department='IT', role='Dev')
        db.session.add(u)
        db.session.commit()
        
        evaluate_all_user_risks()
        res = RiskResult.query.filter_by(user_id='UTEST01').first()
        self.assertIsNotNone(res)
        self.assertGreaterEqual(res.risk_score, 0.0)
        self.assertLessEqual(res.risk_score, 100.0)

if __name__ == '__main__':
    unittest.main()

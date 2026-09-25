"""
MSc Final-Year Research Evaluation Script:
Compares detection performance of 4 model configurations against ground-truth CERT insider threat labels.

Configurations Evaluated:
- Model A: Rule-Based Engine Only
- Model B: Rule-Based + Graph Centrality Engine
- Model C: Rule-Based + Behavioral ML Engine (Isolation Forest)
- Model D: SecGraph Hybrid Engine (Rule + Graph + ML)
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, RiskResult
from app.evaluation_engine import load_ground_truth_labels

def run_evaluation():
    app = create_app()
    with app.app_context():
        results = RiskResult.query.all()
        if not results:
            print("[!] No risk results found in database. Run analysis first.")
            return

        malicious_users = load_ground_truth_labels()
        data = []
        for r in results:
            is_malicious = 1 if r.user_id in malicious_users else 0
            data.append({
                'user_id': r.user_id,
                'risk_score': r.risk_score,
                'graph_score': r.graph_score,
                'behavior_score': r.behavior_score,
                'rule_score': r.rule_score,
                'is_malicious': is_malicious
            })

        merged = pd.DataFrame(data)
        y_true = merged['is_malicious'].values

        # Model A: Rule Only (> 50 score)
        y_pred_a = (merged['rule_score'] >= 50).astype(int)

        # Model B: Rule + Graph (> 50 weighted score)
        score_b = (0.5 * merged['rule_score']) + (0.5 * merged['graph_score'])
        y_pred_b = (score_b >= 50).astype(int)

        # Model C: Rule + ML (> 50 weighted score)
        score_c = (0.5 * merged['rule_score']) + (0.5 * merged['behavior_score'])
        y_pred_c = (score_c >= 50).astype(int)

        # Model D: Hybrid SecGraph
        y_pred_d = (merged['risk_score'] >= 65).astype(int)

        models = {
            'Model A (Rules Only)': (y_true, y_pred_a, merged['rule_score']),
            'Model B (Rules + Graph)': (y_true, y_pred_b, score_b),
            'Model C (Rules + Behavior ML)': (y_true, y_pred_c, score_c),
            'Model D (SecGraph Hybrid)': (y_true, y_pred_d, merged['risk_score'])
        }

        print("\n" + "="*70)
        print("      SECGRAPH RESEARCH EVALUATION & ABLATION STUDY RESULTS")
        print("="*70)
        print(f"{'Model Architecture':<30} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'ROC-AUC':<10}")
        print("-" * 78)

        for name, (yt, yp, scores) in models.items():
            prec = precision_score(yt, yp, zero_division=0)
            rec = recall_score(yt, yp, zero_division=0)
            f1 = f1_score(yt, yp, zero_division=0)
            try:
                auc = roc_auc_score(yt, scores)
            except Exception:
                auc = 0.5

            print(f"{name:<30} | {prec:<10.4f} | {rec:<10.4f} | {f1:<10.4f} | {auc:<10.4f}")

        print("="*70 + "\n")

if __name__ == '__main__':
    run_evaluation()

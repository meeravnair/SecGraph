import json
from datetime import datetime, timezone
from app.models import db, User, BehaviorFeatures, GraphMetrics, RiskResult, SystemSetting, Alert
from app.behavior_engine import calculate_peer_baselines
from app.ml_engine import predict_anomaly_scores
from app.alert_engine import generate_security_alerts

def calculate_rule_score(user, behavior, graph_metrics, peer_medians):
    """
    Evaluates domain security rules and peer-group deviations.
    Returns (rule_score, list_of_reasons, list_of_recommendations, dict_of_triggered_rules).
    """
    score = 0.0
    reasons = []
    recommendations = []
    triggered = {}
    
    if not behavior:
        return 0.0, ["No behavioral telemetry recorded."], ["Verify monitoring endpoint installation."], {}

    # Rule 1: Excessive After-Hours Activity vs Peer Median (>3x peer median or >5 after-hours)
    peer_after = peer_medians.get('after_hours_count', 2.0)
    rule_after_hours = (behavior.after_hours_count > (peer_after * 2.5) and behavior.after_hours_count >= 4)
    triggered['after_hours'] = {
        'title': 'After-Hours Activity Spike',
        'triggered': rule_after_hours,
        'observed': f"{behavior.after_hours_count} after-hours events",
        'threshold': f"> {peer_after * 2.5:.1f} (peer baseline)",
        'contribution': 25 if rule_after_hours else 0
    }
    if rule_after_hours:
        score += 25
        reasons.append(f"After-hours logins ({behavior.after_hours_count}) exceed peer baseline ({peer_after:.1f}) significantly.")
        recommendations.append("Investigate off-hours authentication sessions and review badge access logs.")

    # Rule 2: Multi-Device Proliferation (>= 3 unique workstations)
    rule_devices = (behavior.unique_devices >= 3)
    triggered['multi_device'] = {
        'title': 'Multi-Device Proliferation',
        'triggered': rule_devices,
        'observed': f"{behavior.unique_devices} workstations",
        'threshold': ">= 3 workstations",
        'contribution': 20 if rule_devices else 0
    }
    if rule_devices:
        score += 20
        reasons.append(f"User authenticated from {behavior.unique_devices} distinct computer workstations.")
        recommendations.append("Verify authorization of secondary workstation devices for lateral movement risk.")

    # Rule 3: High Resource Access Volume (> 12 resources)
    rule_resources = (behavior.unique_resources >= 12 or behavior.file_access_count >= 15)
    triggered['excessive_resource'] = {
        'title': 'Excessive Resource Footprint',
        'triggered': rule_resources,
        'observed': f"{behavior.unique_resources} resources, {behavior.file_access_count} file ops",
        'threshold': ">= 12 resources / 15 ops",
        'contribution': 25 if rule_resources else 0
    }
    if rule_resources:
        score += 25
        reasons.append(f"Unusually broad resource footprint ({behavior.unique_resources} assets accessed).")
        recommendations.append("Audit access permissions and enforce Principle of Least Privilege.")

    # Rule 4: Direct Reachability to Sensitive Resource (Path length == 1)
    has_sensitive = (graph_metrics and graph_metrics.shortest_sensitive_path == 1)
    triggered['sensitive_access'] = {
        'title': 'Sensitive Resource Access',
        'triggered': bool(has_sensitive),
        'observed': "Direct connection (hop distance 1)" if has_sensitive else "No direct path",
        'threshold': "Hop distance == 1",
        'contribution': 30 if has_sensitive else 0
    }
    if has_sensitive:
        score += 30
        reasons.append("Direct active graph edge connecting user to high-value sensitive digital asset.")
        recommendations.append("Verify legitimate business justification for access to confidential data assets.")

    # Rule 5: High Betweenness Centrality (Bridge Account > 0.10)
    is_bridge = (graph_metrics and graph_metrics.betweenness_centrality >= 0.10)
    triggered['graph_bridge'] = {
        'title': 'Graph Bridge Position (Lateral Movement)',
        'triggered': bool(is_bridge),
        'observed': f"Betweenness {graph_metrics.betweenness_centrality if graph_metrics else 0.0:.4f}",
        'threshold': "Betweenness Centrality >= 0.10",
        'contribution': 20 if is_bridge else 0
    }
    if is_bridge:
        score += 20
        reasons.append(f"High graph betweenness centrality ({graph_metrics.betweenness_centrality:.4f}). User acts as a topological bridge.")
        recommendations.append("Inspect user account for lateral movement vulnerabilities across network segments.")

    return min(100.0, score), reasons, recommendations, triggered

def get_security_rules_summary():
    """
    Returns high-level statistics across all 5 domain security rules.
    """
    all_risks = RiskResult.query.all()
    users = User.query.all()
    peer_medians = calculate_peer_baselines()
    
    rules = [
        {'id': 'rule_sensitive', 'title': 'Sensitive Resource Access', 'desc': 'Direct edge to confidential files or databases', 'threshold': 'Hop Distance = 1', 'weight': '+30 pts', 'count': 0},
        {'id': 'rule_resource', 'title': 'Excessive Resource Access', 'desc': 'High volume of distinct file assets accessed', 'threshold': '>= 12 unique resources', 'weight': '+25 pts', 'count': 0},
        {'id': 'rule_after_hours', 'title': 'After-Hours Activity Spike', 'desc': 'Authentications between 18:00 and 07:00', 'threshold': '> 2.5x Peer Baseline', 'weight': '+25 pts', 'count': 0},
        {'id': 'rule_devices', 'title': 'Multi-Device Proliferation', 'desc': 'Multiple distinct computer workstations accessed', 'threshold': '>= 3 workstations', 'weight': '+20 pts', 'count': 0},
        {'id': 'rule_bridge', 'title': 'Graph Bridge Account', 'desc': 'Elevated betweenness centrality in access topology', 'threshold': 'Betweenness >= 0.10', 'weight': '+20 pts', 'count': 0},
    ]

    for u in users:
        behavior = BehaviorFeatures.query.filter_by(user_id=u.user_id).first()
        gm = GraphMetrics.query.filter_by(user_id=u.user_id).first()
        if behavior:
            if gm and gm.shortest_sensitive_path == 1:
                rules[0]['count'] += 1
            if behavior.unique_resources >= 12:
                rules[1]['count'] += 1
            if behavior.after_hours_count > (peer_medians.get('after_hours_count', 2.0) * 2.5):
                rules[2]['count'] += 1
            if behavior.unique_devices >= 3:
                rules[3]['count'] += 1
            if gm and gm.betweenness_centrality >= 0.10:
                rules[4]['count'] += 1

    return rules

def evaluate_all_user_risks():
    """
    Executes the Hybrid Risk Engine with dynamically configured weights:
    Final Score = (w_graph * Graph) + (w_behavior * Behavior ML) + (w_rule * Rule)
    Categorizes into LOW, MEDIUM, HIGH based on configurable thresholds.
    """
    settings = SystemSetting.get_settings()
    w_graph = settings.w_graph
    w_behavior = settings.w_behavior
    w_rule = settings.w_rule
    thresh_low = settings.thresh_low
    thresh_high = settings.thresh_high

    anomaly_scores = predict_anomaly_scores()
    peer_medians = calculate_peer_baselines()
    users = User.query.all()

    high_cnt = 0
    med_cnt = 0
    low_cnt = 0
    anomaly_cnt = 0

    for u in users:
        behavior = BehaviorFeatures.query.filter_by(user_id=u.user_id).first()
        graph_metrics = GraphMetrics.query.filter_by(user_id=u.user_id).first()
        
        # 1. Graph Score (0 - 100)
        g_score = graph_metrics.graph_risk_component if graph_metrics else 0.0
        
        # 2. Behavior Score from ML Isolation Forest (0 - 100)
        b_score = anomaly_scores.get(u.user_id, 0.0)
        if b_score >= 50.0:
            anomaly_cnt += 1
        
        # 3. Rule Score (0 - 100)
        r_score, reasons, recs, triggered_rules = calculate_rule_score(u, behavior, graph_metrics, peer_medians)
        
        # 4. Calibrated Hybrid Fusion
        final_score = round((w_graph * g_score) + (w_behavior * b_score) + (w_rule * r_score), 2)
        final_score = min(100.0, max(0.0, final_score))
        
        # Risk Band Assignment (Table 3.11 in report)
        if final_score >= thresh_high:
            level = 'HIGH'
            high_cnt += 1
            recs = [
                "Immediate SOC analyst review required within 4 hours SLA",
                "Enforce mandatory step-up Multi-Factor Authentication (MFA)",
                "Audit Active Directory group memberships and revoke sensitive file share access",
                "Quarantine associated workstation endpoint for digital forensic imaging"
            ]
        elif final_score > thresh_low:
            level = 'MEDIUM'
            med_cnt += 1
            recs = [
                "Flagged for secondary peer review during scheduled audits (72 Hours SLA)",
                "Review user authentication patterns against departmental peers",
                "Verify legitimate business need for accessed resources during audit cycle"
            ]
        else:
            level = 'LOW'
            low_cnt += 1
            recs = [
                "Baseline activity. Routine continuous logging. No analyst intervention required."
            ]
            
        # Store / Update RiskResult
        rr = RiskResult.query.filter_by(user_id=u.user_id).first()
        if not rr:
            rr = RiskResult()
            rr.user_id = u.user_id
            db.session.add(rr)
            
        rr.risk_score = final_score
        rr.risk_level = level
        rr.graph_score = round(g_score, 2)
        rr.behavior_score = round(b_score, 2)
        rr.rule_score = round(r_score, 2)
        rr.anomaly_score = round(b_score, 2)
        rr.reasons_json = json.dumps(reasons)
        rr.recommendations_json = json.dumps(recs)
        rr.analyzed_at = datetime.now(timezone.utc)

        # Trigger security alerts for elevated entities
        generate_security_alerts(u.user_id, final_score, level, reasons)

    db.session.commit()
    return {
        'total_users': len(users),
        'high_count': high_cnt,
        'medium_count': med_cnt,
        'low_count': low_cnt,
        'anomaly_count': anomaly_cnt
    }

def get_user_risk_explanation_payload(user_id):
    """
    Returns the exact JSON Risk Explanation Payload matching Appendix B.1 of the report.
    """
    u = User.query.filter_by(user_id=user_id).first()
    r = RiskResult.query.filter_by(user_id=user_id).first()
    if not u or not r:
        return None

    reasons = json.loads(r.reasons_json) if r.reasons_json else []
    recommendations = json.loads(r.recommendations_json) if r.recommendations_json else []

    return {
        "user_id": r.user_id,
        "risk_score": r.risk_score,
        "risk_level": r.risk_level,
        "components": {
            "graph_score": r.graph_score,
            "behavior_score": r.behavior_score,
            "rule_score": r.rule_score
        },
        "reasons": reasons,
        "recommendations": recommendations
    }

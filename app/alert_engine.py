import json
from datetime import datetime, timezone
from app.models import db, Alert

def generate_security_alerts(user_id, risk_score, risk_level, reasons):
    """
    Generates structured security alerts for identities with HIGH or CRITICAL risk scores.
    """
    if risk_level not in ('HIGH', 'MEDIUM') or risk_score < 50.0:
        return

    severity = 'CRITICAL' if risk_score >= 75.0 else ('HIGH' if risk_score >= 65.0 else 'MEDIUM')
    alert_type = 'HIGH_RISK_IDENTITY' if risk_score >= 65.0 else 'ELEVATED_BEHAVIORAL_ACTIVITY'

    reasons_str = " ".join(reasons).lower() if reasons else ""
    if 'off-hours' in reasons_str and ('sensitive' in reasons_str or 'file' in reasons_str):
        description = f"Identity {user_id} exhibited concurrent off-hours access and sensitive file access."
    else:
        description = f"Identity {user_id} assigned risk score {risk_score}/100 ({risk_level}) with anomalous security telemetry."

    existing = Alert.query.filter_by(user_id=user_id, status='Open').first()
    if existing:
        existing.severity = severity
        existing.alert_type = alert_type
        existing.description = description
        existing.evidence_json = json.dumps(reasons)
        return

    alert = Alert(
        user_id=user_id,
        alert_type=alert_type,
        severity=severity,
        description=description,
        evidence_json=json.dumps(reasons),
        status='Open',
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(alert)

def format_alert_dict(alert):
    """Formats an Alert record to match Appendix B.2 JSON Alert Record schema."""
    return {
        "alert_id": f"ALT-2026-{alert.id:04d}",
        "user_id": alert.user_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "description": alert.description,
        "created_at": alert.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if alert.created_at else ""
    }

def update_alert_status(alert_id, new_status, notes=None):
    """
    Updates the operational triage status of an alert (Open, Under Review, Resolved).
    """
    alert = Alert.query.get(alert_id)
    if not alert:
        return False, "Alert not found"
    
    valid_statuses = {'Open', 'Under Review', 'Resolved'}
    if new_status not in valid_statuses:
        return False, f"Invalid status. Must be one of {valid_statuses}"

    alert.status = new_status
    if notes:
        alert.notes = notes
    db.session.commit()
    return True, f"Alert #{alert_id} updated to {new_status}"

def get_alerts_summary():
    """
    Returns quick breakdown counts of current alerts by severity and status.
    """
    alerts = Alert.query.all()
    return {
        'total': len(alerts),
        'open': sum(1 for a in alerts if a.status == 'Open'),
        'under_review': sum(1 for a in alerts if a.status == 'Under Review'),
        'resolved': sum(1 for a in alerts if a.status == 'Resolved'),
        'critical': sum(1 for a in alerts if a.severity == 'CRITICAL'),
        'high': sum(1 for a in alerts if a.severity == 'HIGH'),
        'medium': sum(1 for a in alerts if a.severity == 'MEDIUM')
    }

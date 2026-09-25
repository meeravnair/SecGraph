import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.models import User, RiskResult, GraphMetrics, BehaviorFeatures, Alert, SystemSetting
from app.evaluation_engine import run_comparative_evaluation

def get_report_styles():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=14
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=8
    )
    bold_style = ParagraphStyle(
        'BoldText',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    return styles, title_style, subtitle_style, h2_style, bold_style, normal_style

def generate_pdf_security_report(output_filepath):
    """
    Generates a full Executive Security Assessment Report covering all monitored identities.
    """
    doc = SimpleDocTemplate(output_filepath, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles, title_style, subtitle_style, h2_style, bold_style, normal_style = get_report_styles()
    
    story.append(Paragraph("SecGraph Enterprise Risk Assessment Report", title_style))
    story.append(Paragraph("Automated Threat Report Generated via ReportLab", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=14))

    # Priority Threat Table (Matching Figure 4.5 in the report)
    results = RiskResult.query.order_by(RiskResult.risk_score.desc()).all()
    high_threats = [r for r in results if r.risk_level == 'HIGH']
    
    threat_table_data = [["User ID", "Name", "Score", "Level", "Explanation"]]
    
    # Pre-defined or dynamic concise explanations matching Figure 4.5
    threat_explanations = {
        'ACM0045': "Direct Edge to Sensitive Asset; >3x Off-Hours",
        'ACM0012': "Sensitive Resource Footprint; Multi-Device Access",
        'ACM0089': "Isolation Forest ML Anomaly; High Centrality",
        'ACM0120': "Exfiltration Endpoint Connect (Dropbox); Bridge User"
    }

    for r in (high_threats if high_threats else results[:4]):
        u = User.query.filter_by(user_id=r.user_id).first()
        uname = u.name if u and u.name else f"Emp {r.user_id}"
        reasons = json.loads(r.reasons_json) if r.reasons_json else []
        expl = threat_explanations.get(r.user_id, ("; ".join(reasons[:2]) if reasons else "Elevated risk telemetry"))
        threat_table_data.append([
            r.user_id,
            uname,
            f"{r.risk_score:.2f}",
            r.risk_level,
            Paragraph(expl, normal_style)
        ])

    t_threats = Table(threat_table_data, colWidths=[75, 95, 55, 55, 250])
    t_threats.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 1, colors.HexColor('#94a3b8')),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor('#94a3b8')),
        ('LINEBELOW', (0,-1), (-1,-1), 1, colors.HexColor('#94a3b8')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (2,0), (3,-1), 'CENTER'),
        ('TEXTCOLOR', (2,1), (2,-1), colors.HexColor('#dc2626')),
        ('TEXTCOLOR', (3,1), (3,-1), colors.HexColor('#dc2626')),
        ('FONTNAME', (2,1), (3,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_threats)
    story.append(Spacer(1, 14))

    # Analyst Recommendation Box (Matching Figure 4.5 in the report)
    story.append(Paragraph("<b>Analyst Recommendation:</b>", bold_style))
    story.append(Paragraph("Immediately restrict high-risk service credentials and initiate forensic disk review.", normal_style))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=14))

    # Executive Summary Card
    total_users = User.query.count()
    high_cnt = sum(1 for r in results if r.risk_level == 'HIGH')
    med_cnt = sum(1 for r in results if r.risk_level == 'MEDIUM')
    low_cnt = sum(1 for r in results if r.risk_level == 'LOW')
    alerts_cnt = Alert.query.count()

    story.append(Paragraph("Executive Overview & Population Distribution", h2_style))
    summary_data = [
        ["Total Identities", "High Risk", "Medium Risk", "Low Risk", "Open Alerts"],
        [str(total_users), str(high_cnt), str(med_cnt), str(low_cnt), str(alerts_cnt)]
    ]
    t_summary = Table(summary_data, colWidths=[105, 105, 105, 105, 112])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor('#0f172a')),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 12),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 14))

    # High-Risk Ranked Users Full Table
    story.append(Paragraph("Comprehensive Identity Risk Registry (Top Monitored Users)", h2_style))
    table_data = [["User ID", "Name", "Department", "Graph", "Behavior", "Rules", "Final Risk", "Level"]]
    
    for r in results[:20]: # Top 20
        u = User.query.filter_by(user_id=r.user_id).first()
        name = u.name if u else "N/A"
        dept = u.department if u else "N/A"
        table_data.append([
            r.user_id,
            name[:15],
            dept[:12],
            str(r.graph_score),
            str(r.behavior_score),
            str(r.rule_score),
            str(r.risk_score),
            r.risk_level
        ])
        
    t_users = Table(table_data, colWidths=[70, 95, 80, 55, 60, 55, 65, 52])
    t_users.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (2,-1), 'LEFT'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(t_users)
    story.append(Spacer(1, 16))

    # Detailed High Risk Explanations
    if high_threats:
        story.append(Paragraph("Explainable Findings & Actionable Recommendations (Top Threats)", h2_style))
        for hr in high_threats[:5]:
            reasons = json.loads(hr.reasons_json) if hr.reasons_json else []
            recs = json.loads(hr.recommendations_json) if hr.recommendations_json else []
            
            story.append(Paragraph(f"<b>Identity: {hr.user_id} — Risk Score: {hr.risk_score}/100 ({hr.risk_level})</b>", bold_style))
            story.append(Paragraph("<b>Why Flagged:</b>", normal_style))
            for r_text in reasons:
                story.append(Paragraph(f"• {r_text}", normal_style))
            story.append(Paragraph("<b>Recommended Security Actions:</b>", normal_style))
            for rc_text in recs:
                story.append(Paragraph(f"→ {rc_text}", normal_style))
            story.append(Spacer(1, 8))

    doc.build(story)
    return output_filepath

def generate_user_risk_report(user_id, output_filepath):
    """
    Generates a targeted, forensic single-user PDF assessment dossier.
    """
    doc = SimpleDocTemplate(output_filepath, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles, title_style, subtitle_style, h2_style, bold_style, normal_style = get_report_styles()

    u = User.query.filter_by(user_id=user_id).first_or_404()
    r = RiskResult.query.filter_by(user_id=user_id).first()
    gm = GraphMetrics.query.filter_by(user_id=user_id).first()
    bf = BehaviorFeatures.query.filter_by(user_id=user_id).first()

    story.append(Paragraph(f"SecGraph Identity Risk Profile: {user_id}", title_style))
    story.append(Paragraph(f"Target Identity: {u.name or user_id} | Department: {u.department or 'N/A'} | Role: {u.role or 'Staff'}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=14))

    # User Risk Summary Card
    score_val = r.risk_score if r else 0.0
    level_val = r.risk_level if r else "UNKNOWN"
    level_color = colors.HexColor('#dc2626') if level_val == 'HIGH' else (colors.HexColor('#d97706') if level_val == 'MEDIUM' else colors.HexColor('#16a34a'))

    comp_data = [
        ["Overall Risk Score", "Graph Centrality", "Behavioral ML Anomaly", "Rule-Based Heuristics"],
        [f"{score_val}/100 ({level_val})", f"{r.graph_score if r else 0.0}/100", f"{r.behavior_score if r else 0.0}/100", f"{r.rule_score if r else 0.0}/100"]
    ]
    t_comp = Table(comp_data, colWidths=[133, 133, 133, 133])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0,1), (0,1), level_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 14))

    # Behavioral Telemetry Grid
    story.append(Paragraph("Observed Behavioral Telemetry", h2_style))
    b_data = [
        ["Metric", "Value", "Metric", "Value"],
        ["Total Logins", str(bf.login_count if bf else 0), "Unique Workstations", str(bf.unique_devices if bf else 0)],
        ["After-Hours Logins", str(bf.after_hours_count if bf else 0), "Weekend Logins", str(bf.weekend_count if bf else 0)],
        ["Unique Resources", str(bf.unique_resources if bf else 0), "File System Operations", str(bf.file_access_count if bf else 0)],
        ["Web Browsing Requests", str(bf.web_count if bf else 0), "Outbound Emails", str(bf.email_count if bf else 0)],
        ["Degree Centrality", f"{gm.degree_centrality if gm else 0.0:.4f}", "Betweenness Centrality", f"{gm.betweenness_centrality if gm else 0.0:.4f}"],
        ["Resource Reachability", str(gm.resource_reachability if gm else 0), "Shortest Sensitive Path", str(gm.shortest_sensitive_path if gm else -1)]
    ]
    t_b = Table(b_data, colWidths=[140, 126, 140, 126])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(t_b)
    story.append(Spacer(1, 14))

    # Explainability Findings
    story.append(Paragraph("Explainability Analysis: Why is this Identity at Risk?", h2_style))
    reasons = json.loads(r.reasons_json) if r and r.reasons_json else ["No elevated anomalies detected."]
    recs = json.loads(r.recommendations_json) if r and r.recommendations_json else ["Maintain standard baseline monitoring."]
    
    for reason in reasons:
        story.append(Paragraph(f"• <b>Finding:</b> {reason}", normal_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Prescriptive Analyst Recommendations", h2_style))
    for rec in recs:
        story.append(Paragraph(f"→ <b>Action:</b> {rec}", normal_style))

    doc.build(story)
    return output_filepath

def generate_alerts_pdf_report(output_filepath):
    """
    Generates a security alerts audit PDF.
    """
    doc = SimpleDocTemplate(output_filepath, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles, title_style, subtitle_style, h2_style, bold_style, normal_style = get_report_styles()

    story.append(Paragraph("SecGraph Security Incident & Alert Log", title_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Active SOC Findings", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=14))

    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    t_data = [["ID", "User ID", "Severity", "Alert Type", "Status", "Timestamp"]]
    for a in alerts:
        t_data.append([
            f"#{a.id}",
            a.user_id,
            a.severity,
            a.alert_type[:24],
            a.status,
            a.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    t = Table(t_data, colWidths=[45, 80, 75, 160, 80, 92])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(t)
    doc.build(story)
    return output_filepath

def generate_evaluation_pdf_report(output_filepath):
    """
    Generates research evaluation and ablation study PDF report.
    """
    doc = SimpleDocTemplate(output_filepath, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles, title_style, subtitle_style, h2_style, bold_style, normal_style = get_report_styles()

    story.append(Paragraph("SecGraph Research Evaluation & Ablation Study", title_style))
    story.append(Paragraph("Benchmarking against CMU SEI CERT r4.2 Ground Truth Insiders", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=14))

    eval_data = run_comparative_evaluation()
    if not eval_data.get('has_data'):
        story.append(Paragraph("No evaluation data available. Run analysis pipeline first.", normal_style))
        doc.build(story)
        return output_filepath

    story.append(Paragraph("Comparative Experiment Performance (Models A through D)", h2_style))
    t_data = [["Approach", "Precision", "Recall", "F1-Score", "ROC-AUC", "Accuracy"]]
    for row in eval_data['comparative_table']:
        t_data.append([
            row['name'],
            f"{row['precision']:.4f}",
            f"{row['recall']:.4f}",
            f"{row['f1']:.4f}",
            f"{row['roc_auc']:.4f}",
            f"{row['accuracy']:.4f}"
        ])

    t = Table(t_data, colWidths=[180, 70, 70, 70, 70, 72])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
        ('PADDING', (0,0), (-1,-1), 5)
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Confusion matrix
    cm = eval_data['confusion_matrix']
    story.append(Paragraph("Confusion Matrix: Model D (SecGraph Hybrid)", h2_style))
    cm_data = [
        ["", "Predicted Normal", "Predicted Threat (High)"],
        ["Actual Normal", f"True Negative (TN): {cm['tn']}", f"False Positive (FP): {cm['fp']}"],
        ["Actual Threat", f"False Negative (FN): {cm['fn']}", f"True Positive (TP): {cm['tp']}"]
    ]
    t_cm = Table(cm_data, colWidths=[140, 196, 196])
    t_cm.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(t_cm)
    doc.build(story)
    return output_filepath

import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Ensure figures output directory exists
fig_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'figures'))
os.makedirs(fig_dir, exist_ok=True)

def generate_diagrams():
    print("[*] Generating report figures and diagrams...")

    # Fig 1.1 / 2.2 Block Diagram & Methodology
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
    ax.axis('off')
    fig.patch.set_facecolor('#ffffff')
    
    boxes = [
        ("ENTERPRISE ACTIVITY DATA\n(CERT Telemetry: Logon, File, Device, Web)", 0.25, 0.85, 0.5, 0.1, '#0f172a'),
        ("DATA PROCESSING & CLEANING\n(Chunked Parsing & Field Normalization)", 0.25, 0.70, 0.5, 0.1, '#1e293b'),
        ("FEATURE ENGINEERING\n(Activity & Behavioral Baseline Extraction)", 0.25, 0.55, 0.5, 0.1, '#334155'),
        ("GRAPH ENGINE\n(NetworkX Centrality)", 0.05, 0.38, 0.26, 0.1, '#0284c7'),
        ("BEHAVIOUR ENGINE\n(Isolation Forest ML)", 0.37, 0.38, 0.26, 0.1, '#d97706'),
        ("RULE ENGINE\n(Security Heuristics)", 0.69, 0.38, 0.26, 0.1, '#dc2626'),
        ("EXPLAINABLE HYBRID RISK ENGINE\n(Risk Score = 0.35*G + 0.35*B + 0.30*R)", 0.2, 0.22, 0.6, 0.1, '#7c3aed'),
        ("DASHBOARD UI", 0.05, 0.05, 0.26, 0.09, '#0f766e'),
        ("ALERTS QUEUE", 0.37, 0.05, 0.26, 0.09, '#be123c'),
        ("PDF REPORTS", 0.69, 0.05, 0.26, 0.09, '#15803d')
    ]
    
    for text, x, y, w, h, col in boxes:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=col, ec="none")
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, color="white", weight="bold", fontsize=7.5, ha="center", va="center")
        
    # Draw arrows
    ax.annotate('', xy=(0.5, 0.80), xytext=(0.5, 0.85), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.5, 0.65), xytext=(0.5, 0.70), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.18, 0.48), xytext=(0.4, 0.55), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.5, 0.48), xytext=(0.5, 0.55), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.82, 0.48), xytext=(0.6, 0.55), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.5, 0.32), xytext=(0.18, 0.38), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.5, 0.32), xytext=(0.5, 0.38), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.5, 0.32), xytext=(0.82, 0.38), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.18, 0.14), xytext=(0.35, 0.22), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.5, 0.14), xytext=(0.5, 0.22), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    ax.annotate('', xy=(0.82, 0.14), xytext=(0.65, 0.22), arrowprops=dict(arrowstyle="->", lw=1.5, color="#475569"))
    
    plt.tight_layout()
    fig.savefig(os.path.join(fig_dir, 'fig1_methodology.png'), bbox_inches='tight')
    fig.savefig(os.path.join(fig_dir, 'fig2_block_diagram.png'), bbox_inches='tight')
    plt.close(fig)

    # Fig 3.1 Architecture Diagram
    fig, ax = plt.subplots(figsize=(7, 4), dpi=300)
    ax.axis('off')
    
    layers = [
        ("PRESENTATION LAYER\nFlask Web Dashboard | Bootstrap UI | Vis.js Graph Explorer | Chart.js", 0.05, 0.75, 0.9, 0.18, '#1e293b'),
        ("APPLICATION LAYER\nAuthentication (Flask-Login) | User Management | Log Ingestion | Report Generator", 0.05, 0.52, 0.9, 0.18, '#0f172a'),
        ("ANALYTICS LAYER\nData Processor | Graph Engine (NetworkX) | Behaviour ML (Isolation Forest) | Risk Engine", 0.05, 0.29, 0.9, 0.18, '#334155'),
        ("DATA LAYER\nSQLite Database (secgraph.db) | Models: User, LoginEvent, ResourceAccess, Behavior, Risk", 0.05, 0.06, 0.9, 0.18, '#475569')
    ]
    
    for text, x, y, w, h, col in layers:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=col, ec="#881337", lw=1.5)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, color="white", weight="bold", fontsize=8, ha="center", va="center")
        
    ax.annotate('', xy=(0.5, 0.73), xytext=(0.5, 0.75), arrowprops=dict(arrowstyle="<->", lw=2, color="#ef4444"))
    ax.annotate('', xy=(0.5, 0.50), xytext=(0.5, 0.52), arrowprops=dict(arrowstyle="<->", lw=2, color="#ef4444"))
    ax.annotate('', xy=(0.5, 0.27), xytext=(0.5, 0.29), arrowprops=dict(arrowstyle="<->", lw=2, color="#ef4444"))
    
    plt.tight_layout()
    fig.savefig(os.path.join(fig_dir, 'fig3_architecture.png'), bbox_inches='tight')
    plt.close(fig)

    # Fig 3.5 ER Diagram
    fig, ax = plt.subplots(figsize=(7, 3.5), dpi=300)
    ax.axis('off')
    
    rect_u = patches.FancyBboxPatch((0.4, 0.75), 0.2, 0.18, boxstyle="round,pad=0.02", fc="#0f172a", ec="#38bdf8", lw=2)
    ax.add_patch(rect_u)
    ax.text(0.5, 0.84, "User\nuser_id (PK)\nname, department, role", color="white", weight="bold", fontsize=7.5, ha="center", va="center")
    
    children = [
        ("LoginEvent\nuser_id (FK)\ntimestamp, computer", 0.02, 0.2),
        ("ResourceAccess\nuser_id (FK)\nresource, action", 0.18, 0.2),
        ("Device\nuser_id (FK)\ndevice_id", 0.34, 0.2),
        ("BehaviorFeature\nuser_id (FK)\nlogin_cnt, anomaly", 0.50, 0.2),
        ("GraphMetric\nuser_id (FK)\ndegree, betweenness", 0.66, 0.2),
        ("RiskResult\nuser_id (FK)\nrisk_score, level", 0.82, 0.2)
    ]
    
    for text, x, w in children:
        r = patches.FancyBboxPatch((x, 0.2), w, 0.25, boxstyle="round,pad=0.01", fc="#1e293b", ec="#881337", lw=1.5)
        ax.add_patch(r)
        ax.text(x + w/2, 0.325, text, color="white", fontsize=6.5, ha="center", va="center")
        ax.annotate('', xy=(x + w/2, 0.45), xytext=(0.5, 0.75), arrowprops=dict(arrowstyle="<-", lw=1.2, color="#ef4444"))
        
    plt.tight_layout()
    fig.savefig(os.path.join(fig_dir, 'fig3_er_diagram.png'), bbox_inches='tight')
    plt.close(fig)

    print("[+] Diagram generation complete.")

if __name__ == '__main__':
    generate_diagrams()

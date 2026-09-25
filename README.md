# SecGraph: Enterprise Identity and Access Risk Analyzer

### Explainable Hybrid Graph and Behavioral Analytics for Enterprise Identity Risk Assessment

SecGraph is a cybersecurity analytics platform developed as an MSc project for assessing enterprise identity and access risk.

The system combines **graph-based identity analysis, behavioral anomaly detection, rule-based security analysis, and explainable risk scoring** to identify potentially high-risk user activity and provide security analysts with contextual information for investigation.

> **Note:** A high-risk score is an analytical indicator and does not by itself establish malicious intent. The system is intended to support authorized security analysis and investigation.

---

## Overview

Enterprise environments generate large volumes of security and identity-related activity involving users, devices, resources, authentication events, and access operations.

Analyzing these activities using only individual events or predefined rules can make it difficult to understand the broader relationships and behavioral patterns associated with an identity.

SecGraph addresses this challenge through a hybrid analytical framework that combines:

- Identity and access graph analysis
- Behavioral feature analysis
- Machine learning-based anomaly detection
- Rule-based security analysis
- Explainable hybrid risk scoring
- Security alerts and reporting

The system converts enterprise activity data into structured user profiles, identity relationships, behavioral features, and risk indicators.

---

## Problem Statement

Enterprise identity environments contain complex relationships between users, devices, resources, roles, and access activities.

Traditional security monitoring approaches may analyze events independently, making it difficult to identify:

- Unusual user behavior
- Excessive resource access
- Unusual device usage
- After-hours activity
- Relationships between users and sensitive resources
- Structurally significant identities
- Combined behavioral and access-related risk

Therefore, SecGraph investigates a hybrid approach that combines **graph analytics, behavioral anomaly detection, and rule-based security indicators** to provide an explainable assessment of enterprise identity risk.

---

## Objectives

The main objectives of SecGraph are:

1. Process and prepare enterprise activity data for security analysis.
2. Extract identity and behavioral features from activity logs.
3. Construct a graph representing relationships between users, devices, and resources.
4. Apply graph analytics to identify structurally significant identities.
5. Generate behavioral profiles for users.
6. Detect unusual behavioral patterns using Isolation Forest.
7. Apply rule-based security indicators.
8. Combine graph, behavioral, and rule-based risk components.
9. Generate an explainable risk score for each analyzed user.
10. Provide dashboards, user profiles, alerts, visualizations, and reports.

---

# Key Features

## 1. Secure Authentication

- Analyst login
- Password hashing
- Session management
- Protected application routes
- Input validation

## 2. Dataset Management

- Dataset upload
- File validation
- Dataset preview
- Data validation
- Timestamp processing
- Data preprocessing

## 3. Identity Graph

SecGraph represents identity and access relationships using a graph structure.

Example relationships include:

```text
USER ──USES──> DEVICE

USER ──ACCESSES──> RESOURCE

USER ──HAS_ROLE──> ROLE

USER ──BELONGS_TO──> DEPARTMENT

1. **Graph-Based Identity & Access Modeling**: Computes Degree Centrality, Betweenness Centrality, Shortest Path to sensitive assets, and Reachability using **NetworkX**.
2. **Unsupervised Behavioral Anomaly Detection**: Trains an **Isolation Forest** on user activity metrics (after-hours logins, multi-device usage, resource volume) without relying on ground-truth labels during training.
3. **Explainable Hybrid Risk Engine**: Combines Graph Risk (35%), Behavioral Anomaly Score (35%), and Rule-Based Security Findings (30%) into a normalized 0–100 risk score with natural-language explanations and recommendations.
4. **Interactive Dashboard & Access Explorer**: Bootstrap 5 web interface with Vis.js interactive network graph visualizer.
5. **Automated Security Reports**: Generates downloadable PDF security assessment reports via **ReportLab**.
6. **MSc Evaluation & Ablation Study**: Evaluates detection performance (Precision, Recall, F1, ROC-AUC) against CMU SEI CERT Insider Threat ground truth.

## Project Structure

```text
SecGraph/
├── app/                  # Application core modules (engine logic, database models, routes)
├── templates/            # HTML templates
├── static/               # CSS and JavaScript assets
├── data/                 # Raw and processed dataset files
├── scripts/              # Dataset inspection, processing, and evaluation scripts
├── tests/                # Unit test suite
├── instance/             # SQLite database instance
└── run.py                # Main application entry point

```
## System Architecture
                    ENTERPRISE ACTIVITY DATA
                              │
                              ▼
                    ┌───────────────────┐
                    │  Data Processing  │
                    │   & Validation    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Feature Engineering│
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │   Graph    │  │ Behavioral │  │    Rule    │
       │  Analysis  │  │  Analysis  │  │   Engine   │
       └─────┬──────┘  └──────┬─────┘  └──────┬─────┘
             │                │               │
             │         ┌──────▼──────┐        │
             │         │  Isolation  │        │
             │         │    Forest   │        │
             │         └──────┬──────┘        │
             │                │               │
             └────────────────┼───────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  Hybrid Risk      │
                    │      Engine       │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ Explainable Risk  │
                    │    Assessment     │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
         Dashboard         Alerts           Reports
              │
              ▼
       User Risk Profiles
       Identity Graph
       Evaluation

## Processing Pipeline

The complete analytical workflow is:

Dataset Upload
      ↓
Data Validation
      ↓
Data Preprocessing
      ↓
Feature Engineering
      ↓
Identity Graph Construction
      ↓
Graph Analytics
      ↓
Behavioral Feature Generation
      ↓
Isolation Forest
      ↓
Rule-Based Analysis
      ↓
Hybrid Risk Calculation
      ↓
Risk Classification
      ↓
Explainability
      ↓
Dashboard / Alerts / Reports


## Risk Scoring

SecGraph combines three major analytical components:

Graph Risk

Represents risk-related indicators obtained from identity and access relationships.

Behavioral Risk

Represents unusual behavioral activity identified through behavioral analysis and anomaly detection.

Rule Risk

Represents security indicators identified through predefined analytical rules.

The current hybrid risk model uses:

Final Risk Score =
    0.35 × Graph Score
  + 0.35 × Behavioral Score
  + 0.30 × Rule Score
Risk Classification
Risk Score	Risk Level
0 – 34.9	Low
35 – 64.9	Medium
65 – 100	High

## Quick Start Guide

### 1. Activate Virtual Environment & Install Dependencies
```powershell
venv\Scripts\activate
pip install --default-timeout=100 -r requirements.txt
```

### 2. Launch the Application
```powershell
python run.py
```

### 3. Log In to Dashboard
* URL: `http://127.0.0.1:5000/login`
* Default Credentials:
  * Username: `meera` | Password: `meera123`
  * Username: `admin` | Password: `admin123`

### 4. Run MSc Comprehensive Test Suite (Table 5.1)
```powershell
python -m unittest discover tests
```
*Executes all 12 unit and system test cases (TC01 - TC12) with a 100% success rate.*

### 5. Run MSc Evaluation & Ablation Harness
```powershell
python scripts/evaluate.py
```

### 6. REST API Endpoints (Appendix B)
* `GET /api/user/<user_id>/explanation`: JSON Risk Explanation Payload (Appendix B.1)
* `GET /api/alerts`: Formatted JSON Security Alerts Log (Appendix B.2)
* `GET /api/alert/<alert_id>`: Individual JSON Alert Record
* `GET /api/graph/metrics/<user_id>`: Topological Graph Metrics (Table 4.3)


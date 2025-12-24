# 🚀 Startup Investment Analytics & Forecasting Platform

A comprehensive data intelligence platform designed to analyze, track, and forecast Indian startup funding trends. This project integrates end-to-end data pipelines: from Selenium-based web scraping and advanced feature engineering to AI-powered predictive modeling and a multi-page interactive Streamlit dashboard.

---

## 🌟 Key Features

- 📊 **Interactive Dashboards**  
  High-level overviews of funding trends, sector allocations, and investor activities across India.

- 🏢 **Company & Investor Explorer**  
  Deep-dive into specific startup histories and investor portfolios, featuring co-investment networks and similar peer discovery.

- 🌍 **Market Intelligence**  
  Analyze funding "hotspots" across different headquarters and sector combinations using rolling market signals and momentum heatmaps.

- 🔮 **AI Forecasting (XGBoost)**  
  - Probability of a startup raising another round within 12 months  
  - Estimated amount of the next funding round  
  - Investment Success Score based on historical success metrics

- 🎯 **Personalized Recommendations**  
  A "For You" engine using:
  - User preferences (sectors, stages, budget)
  - User activity logs (views, filters, searches)

- 🔒 **Secure Onboarding**  
  Built-in authentication and multi-step onboarding to capture:
  - User interests  
  - Investment goals  
  - Experience levels  

---

## 🏗️ Technical Architecture

### 1. Data Engineering (Scraping & Cleaning)

- **Scraping**  
  Automated Selenium scripts scraping **10+ years (2015–2025)** of data from *StartupTalky*

- **Cleaning**
  - Handles multiple currencies (USD, INR, SGD)
  - Standardizes company names using **RapidFuzz**
  - Maps **1000+ sub-sectors** into clean industry buckets

- **Feature Engineering**
  - Rolling **6-month & 12-month** market signals
  - Funding totals, round counts, median sizes
  - Captures momentum and seasonality

---

### 2. Machine Learning (XGBoost Pipeline)

- **Classification**
  - Predicts *Will Raise Again*
  - AUC ≈ **0.97**

- **Regression**
  - Predicts *Next Round Amount*
  - R² ≈ **0.95**

- **Preprocessing**
  - Scikit-learn pipelines
  - `ColumnTransformer`
  - One-hot encoding & feature scaling

---

### 3. Database Layer (MySQL / PostgreSQL)

Used to manage **dynamic application state**:

- User Profiles & Authentication
- User Preferences (sector, stage, risk)
- Activity Logging (clicks, views, searches)
- Watchlists for startups
- Feedback loops to improve recommendations

---

### 4. Frontend (Streamlit Dashboard)

- Multi-page application structure for seamless navigation.
- Customized components for KPI cards, activity logging, and personalized UI blocks.
- Interactive visualizations powered by Plotly.

---

## 🔄 Project Workflow

1. **Data Acquisition** – Selenium scripts crawl web sources to build the raw funding database.
2. **Processing & Enhancement** – Data is cleaned, currencies standardized to INR (Cr), and rolling market signals are computed.
3. **Model Training** – XGBoost models are trained on historical "Next Round" outcomes to create the forecasting engine.
4. **User Onboarding** – Users sign up and define their investment profile (e.g., "Seed stage AI startups in Bangalore").
5. **Intelligence Delivery** – The dashboard combines static funding data with real-time AI forecasts and personalized recommendations based on the user's SQL-stored profile.

---

## 📁 Project Structure
``` bash
├── app.py # Streamlit entry point & Auth logic
├── auth/ # Authentication configs
├── pages/ # Multi-page dashboard modules
│ ├── 1_Overview.py
│ ├── 2_Companies.py
│ ├── 3_Investors.py
│ ├── 4_Markets.py
│ ├── 5_Forecasting.py
│ ├── 6_Deal_Explorer.py
│ ├── 6_For_You.py
│ └── 7_Onboarding.py
├── utils/
│ ├── db.py # SQL operations & logging
│ ├── helper.py # UI helpers
│ ├── load_data.py # Data loading
│ ├── ml_models.py # Model inference
│ └── sidebar.py
├── notebooks/
│ ├── Scraping.ipynb
│ ├── Feature_Eng.ipynb
│ └── ML_Models.ipynb
├── models/ # Serialized XGBoost models
├── data/ # Processed CSV datasets
└── requirements.txt
```
---

## 🚀 Getting Started

### Prerequisites

- Python **3.9+**
- Google Chrome (for Selenium)
- MySQL or PostgreSQL

### Installation

### 1.Clone the repository:
```bash
git clone https://github.com/your-username/startup-analytics-platform.git
cd startup-analytics-platform
```

### 2.Install dependencies:
``` bash
pip install -r requirements.txt
```

### 3.Run the application:
``` bash
streamlit run app.py
```

### 📈 Model Performance
``` bash
Model Task	                  Metric	           Value
Funding Classifier	          Accuracy	         0.906
Funding Classifier	          AUC	               0.973
Amount Regressor	            R²	               0.958
Success Scorer	              AUC	               0.973
```

### 🤝 Contact
Email: keyurkorat1660gmail.com

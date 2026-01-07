# LogisticsPro - Fleet Management System

## 🚀 Executive Summary
LogisticsPro is a specialized "Control Tower" operations platform designed for the KZN logistics sector. It replaces manual spreadsheet tracking and WhatsApp chaos with a centralized digital system, ensuring real-time visibility, driver accountability, and audit-ready Proof of Delivery (POD).

---

## 🎯 Who This Is For (Ideal Customer Profile)
**Small to Medium Logistics & Delivery Businesses**
* **Fleet Size:** 3–30 vehicles.
* **Region:** Operating primarily in KwaZulu-Natal (Durban/Richards Bay corridor).
* **Current State:** Reliant on manual spreadsheets, phone calls, and WhatsApp groups.
* **The Problem:** Owners cannot verify where drivers are, if goods were delivered, or why trips are delayed.

---

## 📉 The Pain in Numbers
Why this software exists:
* **10–25% Revenue Loss:** Fleets lose significant revenue annually due to poor performance visibility and "dead miles."
* **4+ Hours/Week:** The average owner spends over 4 hours just chasing drivers on the phone for status updates.
* **Cash Flow Delays:** Lost or damaged Proof of Delivery (POD) documents delay invoicing by weeks.

**LogisticsPro closes these gaps immediately.**

---

## 📊 Core Metric Dashboard
The system allows owners to visualize the critical financial health of their fleet:
* **Profit per vehicle:** Tracking revenue generated versus operational costs per truck.
* **Cost per trip:** Monitoring fuel, toll, and driver labor costs per specific route.
* **Fuel leakage:** Identifying anomalies in fuel consumption to detect theft or inefficiency.
* **Driver variance:** Comparing planned delivery times against actual arrival times to score driver reliability.

---

## 💼 Business Model
We operate as a high-touch technical partner, not just a software vendor.

**1. Pricing Model**
* **One-time setup & data onboarding:** Fee for server configuration, fleet database creation, and hardware setup.
* **Monthly performance analysis & reporting:** Recurring subscription for hosting, data storage, and automated monthly CSV reports.
* **Optional custom automation:** Add-on services for integration with Sage/Xero or custom route planning logic.

---

# 🗺️ Product Roadmap: LogisticsPro Financial Intelligence

## TIER 0 — MVP (CURRENT STATUS) 🟢
**Goal:** Financial Visibility for Logistics SMEs
* ✅ Manual Job Creation & Revenue Tracking
* ✅ Profit per Job / Vehicle / Driver Calculation
* ✅ Weekly Owner Report (PDF Generation)
* ✅ Red Flags for Margin Leakage (<15%)
* 🔲 **CSV Bulk Data Import** (In Progress)

---

## TIER 1 — RETENTION & TRUST (MONTH 2–3) 🟡
**Goal:** Automated Data Ingestion & Consistency
* **Fuel Card Integration:** Bulk upload of CSV statements (Shell/Engen) to auto-match fuel costs to vehicles.
* **Scheduled Reporting:** Automated email delivery of the "Weekly Owner Report" every Monday at 08:00.
* **Historical Trends:** Visual charts showing Month-over-Month profit variance per vehicle.

---

## TIER 2 — OPERATIONAL INSIGHT (MONTH 4–6) 🔴
**Goal:** Upsell & Contract Value Increase
* **Driver Performance Index (DPI):** Composite score (0-100) based on Profit Contribution + On-Time Rate.
* **Vehicle Health Signals:** Algorithmic flagging of abnormal fuel usage spikes (e.g., "Vehicle B12 is using 15% more fuel than fleet average").
* **SLA Analytics:** Delivery timeline tracking (On-time vs. Late %) to help clients avoid penalties.

---

## TIER 3 — AUTOMATION (MONTH 6–9) 🟣
**Goal:** Premium Automation
* **Exception Alerts:** Real-time Email/Telegram notifications for margin crashes or massive delays.
* **Client Portal (Lite):** Read-only link for *end-clients* to see status and PODs without contacting the office.

---

## TIER 4 — DECISION SUPPORT (MONTH 9–12) 🔵
**Goal:** Advisory & Strategic Value
* **What-If Scenarios:** "Simulator" tool to predict profit impact of route changes or fleet reduction.
* **Cost Forecasting:** Linear regression models to project next month's cash flow requirements.

## 🛠️ Tech Stack
* **Backend:** Python (Flask)
* **Database:** SQLite (Relational Schema with SQLAlchemy)
* **Frontend:** HTML5, Tailwind CSS, JavaScript
* **Geospatial:** Leaflet.js, OpenStreetMap API

---

## 📦 Installation & Setup
1.  **Clone the repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/logistics-fleet-manager.git](https://github.com/YOUR_USERNAME/logistics-fleet-manager.git)
    ```
2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Application**
    ```bash
    python app.py
    ```
4.  **Access the System**
    * **Admin Login:** `admin` / `123`
    * **Browser:** Open `http://127.0.0.1:5001`

---

## 📄 License
**Proprietary Software.** Built specifically for the South African Logistics Market.
*Copyright © 2026 LogisticsPro KZN.*

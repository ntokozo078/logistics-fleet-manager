# LogisticsPro - Fleet Management System

## 🚀 Overview
LogisticsPro is a full-stack fleet management platform designed for the South African logistics SME market. It replaces manual spreadsheet tracking with a centralized "Control Tower" dashboard, enabling real-time status updates, driver identity verification, and digital Proof of Delivery (POD) auditing.

This system solves the critical financial problem of lost paperwork and untracked deliveries in the supply chain.

## 🛠️ Tech Stack
* **Backend:** Python (Flask)
* **Database:** SQLite (Relational Schema with SQLAlchemy ORM)
* **Frontend:** HTML5, Tailwind CSS, JavaScript
* **Geospatial:** Leaflet.js + OpenStreetMap API (Reverse Geocoding & Route Visualization)
* **Data Engineering:** Automated ETL pipeline for CSV reporting (Weekly/Monthly/Yearly)

## ✨ Key Features
### 1. Operations Dashboard (The Control Tower)
* Real-time counters for Active, Delayed, and Completed jobs.
* Role-Based Access Control (RBAC) separating Admin and Driver views.
* Visual status tracking (In Transit / Delivered / Issue).

### 2. Driver Mobile App
* **Zero-Friction Interface:** Simplified UI for drivers on low-end Android devices.
* **Mandatory POD Logic:** System enforces file upload (camera capture) before a job can be marked "Delivered," ensuring data integrity.
* **Interactive History:** Drivers can audit their own past deliveries and uploads.

### 3. Geospatial Route Planning
* Integrated **Leaflet.js** map interface.
* Supports both **Search-based** and **Click-based** location selection.
* Automatically visualizes the route distance with a dynamic polyline connector.

### 4. Data Reporting
* Built-in reporting engine that queries the `Job` entity based on time-series filters (Week/Month/Year).
* Exports clean, structured CSV data compatible with Sage/Xero for invoicing.

## 📦 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/logistics-fleet-manager.git](https://github.com/ntokozo078/logistics-fleet-manager.git)
    cd logistics-fleet-manager
    ```

2.  **Create Virtual Environment (Optional but recommended)**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install flask flask-sqlalchemy werkzeug
    ```

4.  **Run the Application**
    ```bash
    python app.py
    ```

## 🛡️ Database Schema
The system uses a relational model with the following entities:
* **User:** Stores authentication data and roles (Admin/Driver).
* **Job:** The central fact table linking Clients, Drivers, and Statuses. Includes timestamps for SLA tracking.

## 📄 License
Proprietary software built for the KZN Logistics Industry.
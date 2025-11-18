# BudgetBrain V2.0: The AI-Powered Finance Tracker

**BudgetBrain** is a full-stack Django application designed to automate personal finance tracking. It goes beyond simple manual entry by using machine learning to automatically categorize transactions and detect anomalies.

This project was built from scratch to demonstrate advanced proficiency in Python, Django, Data Science (Pandas/Scikit-Learn), and Frontend Development.

---

## 🚀 Key Features

### 🧠 Intelligent AI "Brain"
* **Hybrid AI System:** Combines a "Pre-Trained Brain" (trained on a 24,000-line dataset) for new users with a "Custom Brain" that fine-tunes itself based on user corrections.
* **Dual-Prediction:** Automatically predicts both the **Transaction Type** (Income vs. Expense) and the **Category** (e.g., Groceries, Salary, Utilities).
* **Smart Parsing:** Capable of reading both **CSV** and **PDF** bank statements, including complex layouts with separate Debit/Credit columns.

### 📊 Advanced Dashboard
* **Financial Health:** Real-time summary cards for **Total Income**, **Total Expenses**, and **Net Balance**.
* **Interactive Visualizations:** Dynamic Pie Charts (Spending by Category) and Bar Charts (Spending Over Time) powered by Chart.js.
* **Budget Tracking:** Visual progress bars for each category that turn **RED** when the monthly budget is exceeded.
* **Anomaly Detection:** An algorithmic alert system that flags "Unusual Activity" if current spending exceeds 2x the historical average for a category.

### 🛠️ Powerful Tools
* **Full CRUD:** Users can Create, Read, Update, and Delete transactions.
* **Bulk Management:** A "Save All Changes" feature allows for rapid categorization updates.
* **Smart Filters:** Search transactions by name, category, or date range.
* **Exporters:** Built-in tools to export filtered data to **CSV** or professional **PDF** reports.
* **Financial Calculators:** Integrated tools for Savings Goals and Loan Payments.

### 🎨 Polished UI/UX
* **Responsive Design:** Built with **Pico.css** for a clean, modern mobile-friendly interface.
* **Dark Mode:** A persistent light/dark theme switcher.
* **Custom Styling:** Custom CSS for glowing text effects, hover animations, and status colors (Green for Income, Red for Expense).
* **Global Ready:** A Settings page allows users to customize their **Currency Symbol** ($, ₹, €, etc.).

---

## 🛠️ Tech Stack

* **Backend:** Python, Django
* **Database:** SQLite (Development)
* **Data Science:** Pandas, Scikit-Learn (LinearSVC, TfidfVectorizer)
* **PDF Processing:** pdfplumber, ReportLab
* **Frontend:** HTML5, Pico.css, Chart.js, Custom CSS
* **Version Control:** Git & GitHub

---

## ⚙️ Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/BudgetBrain.git](https://github.com/your-username/BudgetBrain.git)
    cd BudgetBrain
    ```

2.  **Create and activate virtual environment:**
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install django pandas scikit-learn pdfplumber reportlab
    ```

4.  **Apply migrations:**
    ```bash
    python manage.py migrate
    ```

5.  **Run the server:**
    ```bash
    python manage.py runserver
    ```

6.  **Access the app:** Open `http://127.0.0.1:8000/login/` in your browser.

---

## 🧪 How to Test the AI

1.  **Go to Dashboard:** Log in and click **"Delete All Transactions"** to start fresh.
2.  **Upload Data:** Upload the included `test_suite.csv` or `financial_dataset_24000_realistic.csv`.
3.  **Observe:** The AI will instantly categorize thousands of transactions.
4.  **Fine-Tune:** Manually change a category (e.g., mark "Starbucks" as "Shopping" instead of "Restaurants") and click **"Save All Category Changes"**.
5.  **Verify:** Upload a new file with "Starbucks" in it. The AI will now classify it as "Shopping," proving it has learned from you.

---

## 📝 Project Status: COMPLETE

This project includes all planned phases:
* [x] Phase 1-8: Core Platform & CRUD
* [x] Phase 9-12: Powerful Hybrid AI (V2.0)
* [x] Phase 13: Budget Goal System
* [x] Phase 15: CSV & PDF Exporters
* [x] Phase 16: Financial Calculators
* [x] Phase 17: User Settings (Currency)
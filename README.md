# 🛒 SafeCart

### 🤖 AI-Powered E-Commerce Support & Compliance System

SafeCart helps customers get verified information about product prices, stock availability, delivery details, and refund eligibility.

> ⚡ Every customer response is checked by an Auditor Agent before it is shown.

---

## ✨ Features

- 🛒 **Full Amazon-Style Shopping Clone**: Familiar Amazon navigation, live search, department menus, product cards, detail modal, cart, demo checkout, order confirmation, and visual order tracking timeline.
- 🔍 **SafeCart AI Chatbot with ID Lookup**: Direct lookup for any Product ID (`P001`-`P500`) or Order ID (`O001`-`O580`) with interactive product cards and direct-track buttons.
- 🛡️ **Authentication & Order Ownership Gate**: Strict privacy protection requiring verification before disclosing sensitive customer shipping/billing information.
- 🖼️ **500 Unique Product Images**: Every product in `Database/products.csv` has a dedicated, verified image URL with zero duplicates.
- 💰 Product price checking & live stock updates synchronized with orders.
- 📦 Inventory availability validation before checkout.
- 🚚 Order delivery tracking with milestone timeline.
- 💳 Refund eligibility checking against verified policies.
- 🤖 Dual-Agent Governance: Worker AI Agent + Auditor AI Agent workflow.
- 🎨 Modern React interface (`/`) and Amazon Clone interface (`/amazon`).
- ⚡ FastAPI backend with high-speed CSV engine.
- 🗂️ CSV-based single source of truth database.

---

## 🧠 How It Works

```text
👤 Customer Query
       ↓
🤖 Worker Agent checks database
       ↓
🔍 Auditor Agent verifies response
       ↓
✅ Safe and verified customer response
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|------|------------|
| 🎨 Frontend | React + Vite + CSS |
| ⚙️ Backend | Python + FastAPI + Uvicorn |
| 🗂️ Database | CSV files + Pandas |
| 🤖 Agents | Worker Agent + Auditor Agent |

---

## 📁 Project Structure

```text
Sem Project-1/
│
├── frontend/                      # 🎨 React frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   └── components/
│   │       ├── Header.jsx
│   │       ├── CustomerForm.jsx
│   │       ├── ResponseCard.jsx
│   │       ├── AuditInfo.jsx
│   │       └── Sidebar.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/                       # ⚙️ FastAPI backend
│   ├── main.py
│   ├── worker_agent.py
│   ├── auditor_agent.py
│   ├── rules.py
│   └── requirements.txt
│
├── database/                      # 🗂️ CSV data files
│   ├── products.csv
│   ├── inventory.csv
│   ├── orders.csv
│   ├── policies.csv
│   └── database.py
│
├── models/
│   └── schemas.py
│
├── utils/
│   └── helpers.py
│
├── README.md
└── .gitignore

```

---

## 🚀 How to Run SafeCart

### Option A: Development Mode (Recommended for Development)

SafeCart runs with a FastAPI backend and a Vite React frontend:

#### 1. Start the Backend ⚙️
In **Terminal 1** (from project root):
```bash
python -m uvicorn Backend.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Swagger UI Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

#### 2. Start the Frontend 🎨
In **Terminal 2** (from project root):
```bash
cd Frontend
npm install
npm run dev
```
- Open console in browser: `http://localhost:5173`

> [!NOTE]
> Always keep **Terminal 1 (Backend)** running while using the frontend on `http://localhost:5173`. The frontend proxies API requests to port `8000`.

---

### Option B: Single Combined Server (Production / Demo Mode)

You can also run both the Frontend and Backend together on a single port (`8000`):

```bash
# 1. Build the React frontend production bundle
cd Frontend
npm run build
cd ..

# 2. Start the unified server
python -m uvicorn Backend.main:app --port 8000
```
- Open **`http://127.0.0.1:8000`** in your browser to use the full application directly!

---

### Option C: Cloud & Docker Deployment 🌐

SafeCart is fully prepared for instant cloud deployment (Render, Vercel, Railway, Docker, AWS, GCP):

```bash
# 1-command Docker deployment
docker compose up -d --build
```

👉 See the complete step-by-step guide in [DEPLOYMENT.md](file:///c:/Users/fular/OneDrive/Desktop/Sem-Project-1-main/DEPLOYMENT.md) for free 1-click Render and Vercel hosting instructions.

---

### 🧪 Full System Verification & Test Commands

Run the comprehensive master verification suite to validate all database records, AI agents, API routes, Amazon clone integration, and frontend build:

```bash
python run_all_tests.py
```

Run the 13-Point Final Enhancement Verification Suite:
```bash
python test_final_enhancements.py
```

You can also run individual verification test suites:
```bash
# 1. Test database and CSV integrity (500 products, unique images, schema)
python Database/test_database.py

# 2. Test compliance rules engine
python Backend/test_rules.py

# 3. Test Worker AI agent (11 test cases)
python Backend/test_worker.py

# 4. Test Auditor AI agent (7 validation cases)
python Backend/test_auditor.py

# 5. Test FastAPI backend endpoints
python Backend/test_main.py

# 6. Test Amazon Clone & SafeCart Integration (12 test cases)
python -m unittest test_amazon_safecart_integration.py

# 7. Test E2E Shopping & Checkout Demo Journey (9 test cases)
python -m unittest test_e2e_shopping_demo.py
```

---

## 📡 API Usage

### Endpoint

```text
POST /api/chat
```

### Example Request

```json
{
  "query": "What is the price of this product?",
  "product_id": "P001"
}
```

### Example Response

```json
{
  "status": "APPROVED",
  "response": "The price of Wireless Headphones is Rs. 1999.",
  "worker_response": {
    "status": "SUCCESS",
    "intent": "PRICE",
    "product": {
      "product_id": "P001",
      "product_name": "Wireless Headphones",
      "price": 1999
    },
    "database_verified": true
  },
  "audit": {
    "status": "APPROVED",
    "audit_decision": "APPROVED",
    "errors": [],
    "corrections": []
  }
}
```

---

## 💬 Sample Customer Questions & Test Queries

Try entering these realistic customer queries in the console or API:

| Category | Sample Customer Question | Required ID | Expected System Behavior |
|---|---|---|---|
| 💰 **Price Check** | *"What is the price of this product?"* | Product ID: `P001` | Returns verified price (`Rs. 1999`) for Wireless Headphones |
| 💰 **Price Check** | *"How much does the Smart Watch cost?"* | Product ID: `P002` | Returns verified price (`Rs. 2999`) for Smart Watch |
| 📦 **In Stock** | *"Is product P001 available in stock?"* | Product ID: `P001` | Confirms item is in stock (`Available quantity: 25`) |
| 📦 **Out of Stock** | *"Can I buy product P009 right now?"* | Product ID: `P009` | Auditor ensures out-of-stock notification (`Quantity: 0`) |
| 🚚 **Delivery Date** | *"When will my order arrive?"* | Order ID: `O001` | Returns verified delivery date (`2026-09-05`) |
| 🚚 **Delivery Tracking** | *"What is the delivery status of my package?"* | Order ID: `O002` | Looks up expected delivery schedule from orders database |
| 💳 **Refund Eligible** | *"Can I get a refund for my order?"* | Order ID: `O001` | Confirms refund eligibility according to return policy |
| 💳 **Non-Refundable** | *"I want to request a refund for order O010."* | Order ID: `O010` | Auditor blocks false refund; states order is non-refundable |
| 🔄 **Return Policy** | *"What is your return and exchange policy?"* | *(None)* | Returns official 7-day return policy details |
| 🚫 **Invalid Product ID** | *"What is the price of this item?"* | Product ID: `P9999` | Flags invalid Product ID; prompts customer for a valid ID |
| 🚫 **Invalid Order ID** | *"When will my order be delivered?"* | Order ID: `O9999` | Flags invalid Order ID; prevents fabricated delivery dates |
| ❓ **General Help** | *"Hello, what can you help me with?"* | *(None)* | Displays helpful list of supported customer service topics |

---

## 👨‍💻 Group Members

- **Bhushan Fulari**
- **Harshada Dhangar**
- **Purvaja Dutte**
- **Bhavesh Patil**

---

## 🎓 License

This project was created for academic purposes.

⭐ If you like this project, give it a star on GitHub!


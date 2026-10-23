# 🚀 SafeCart Deployment & Verification Guide

SafeCart can be deployed online in multiple production-ready architectures depending on your preferences. Below are complete, step-by-step guides for:
1. **Separated Architecture (Recommended for high performance)**: React/Vite Frontend on **Vercel** or **Netlify** + Python FastAPI Backend on **Render** or **Railway**.
2. **Unified Single-Service Architecture**: Both Frontend and Backend packaged into a single container via **Docker** on **Render**, **Railway**, or **Google Cloud Run**.
3. **Instant Zero-Cost Public Tunnel**: Live public demo via **Cloudflare Tunnel**.

---

## 📋 Table of Contents
1. [Backend Deployment (Render / Railway / Docker)](#1-backend-deployment-fastapi)
2. [Frontend Deployment (Vercel / Netlify)](#2-frontend-deployment-react-vite)
3. [Unified Container Deployment (Render / Cloud Run)](#3-unified-container-deployment)
4. [Environment Variables Reference](#4-environment-variables-reference)
5. [Local Execution Instructions](#5-local-execution-instructions)
6. [Live Application Testing & Verification Checklist](#6-live-application-testing--verification-checklist)
7. [Troubleshooting Common Issues](#7-troubleshooting-common-issues)

---

## 1. Backend Deployment (FastAPI)

### Method A: Deploying Backend to Render (Free Cloud Service)
1. Push your SafeCart repository to your **GitHub** account.
2. Sign up or log in at [Render.com](https://render.com).
3. Click **New +** > **Web Service**.
4. Select **Build and deploy from a Git repository** and connect your repository.
5. In the configuration settings:
   - **Name**: `safecart-api` (or your preferred name)
   - **Region**: Choose the closest region (e.g., Singapore, Frankfurt, Oregon)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (uses repo root)
   - **Runtime**: **Python 3**
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn Backend.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: **Free**
6. Expand **Advanced** > **Environment Variables** and add:
   | Key | Value | Description |
   |---|---|---|
   | `ALLOWED_ORIGINS` | `*` | Or specify your future Vercel/Netlify URL |
   | `PORT` | `8000` | (Render sets this dynamically, but setting default is good practice) |
7. Click **Create Web Service**.
8. Wait for the build logs to show `Application startup complete`.
9. Copy your public backend URL (e.g., `https://safecart-api.onrender.com`).
10. Test in your browser: `https://safecart-api.onrender.com/health` -> should return `{"status":"healthy","service":"SafeCart API"}`.

### Method B: Deploying Backend to Railway
1. Sign up at [Railway.app](https://railway.app).
2. Click **New Project** > **Deploy from GitHub repo**.
3. Select your SafeCart repository.
4. Go to **Settings** > **Deploy**:
   - **Start Command**: `uvicorn Backend.main:app --host 0.0.0.0 --port $PORT`
5. Go to **Variables** and add:
   - `ALLOWED_ORIGINS`: `*`
6. Go to **Settings** > **Networking** > **Generate Domain**.
7. Railway will generate a live HTTPS URL (e.g., `https://safecart-backend.up.railway.app`).

---

## 2. Frontend Deployment (React / Vite)

### Option A: Deploying Frontend to Vercel (Recommended)
1. Log in at [Vercel.com](https://vercel.com).
2. Click **Add New...** > **Project**.
3. Import your SafeCart GitHub repository.
4. In the project configuration modal:
   - **Project Name**: `safecart`
   - **Framework Preset**: **Vite**
   - **Root Directory**: Click *Edit* and select `Frontend`
   - **Build Command**: `vite build` (or `npm run build`)
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
5. Expand **Environment Variables** and add:
   | Key | Value | Note |
   |---|---|---|
   | `VITE_API_BASE_URL` | `https://safecart-api.onrender.com/api` | Replace with your live backend domain from Step 1 |
6. Click **Deploy**.
7. Vercel will build the frontend in ~30 seconds and provide a production HTTPS URL (e.g., `https://safecart.vercel.app`).
8. The project includes [Frontend/vercel.json](file:///c:/Users/fular/OneDrive/Desktop/Sem-Project-1-main/Frontend/vercel.json) to handle single-page application routing without 404s.

### Option B: Deploying Frontend to Netlify
1. Log in at [Netlify.com](https://netlify.com).
2. Click **Add new site** > **Import an existing project**.
3. Choose **GitHub** and select your SafeCart repository.
4. Set the build settings:
   - **Base directory**: `Frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `Frontend/dist`
5. Click **Add environment variable**:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://safecart-api.onrender.com/api`
6. Click **Deploy Site**.
7. Netlify will build your application and assign a live URL (e.g., `https://safecart.netlify.app`). The included `Frontend/public/_redirects` file automatically configures clean client-side routing.

---

## 3. Unified Container Deployment

If you want both the React Frontend and the FastAPI Backend to run inside a single container on a single domain:

### Deploy with Docker to Render:
1. In Render, select **New Web Service**.
2. Connect your repository.
3. Select **Environment**: **Docker**.
4. The service will build from our multi-stage [Dockerfile](file:///c:/Users/fular/OneDrive/Desktop/Sem-Project-1-main/Dockerfile):
   - Stage 1: Builds the React application with Vite into static production assets.
   - Stage 2: Packages the Python 3.11 FastAPI backend, CSV databases, and copies the built frontend into `Frontend/dist`.
5. Fast, self-contained, and no separate CORS configuration required!

### Run with Docker Locally:
```bash
# 1. Build the unified Docker image
docker build -t safecart:latest .

# 2. Run the container on port 8000
docker run -d -p 8000:8000 --name safecart safecart:latest
```
Open `http://localhost:8000` in your browser.

---

## 4. Environment Variables Reference

| Variable | Scope | Default Value | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Frontend | `/api` | Base URL for FastAPI backend endpoints. In production, set to `https://<YOUR-BACKEND-DOMAIN>/api`. |
| `ALLOWED_ORIGINS` | Backend | `*` | Comma-separated list of allowed CORS domains or `*` for all. SafeCart automatically permits Vercel, Netlify, and Render preview domains. |
| `PORT` | Backend | `8000` | Port for the Uvicorn ASGI server to bind to. Set automatically by Render/Railway. |

---

## 5. Local Execution Instructions

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ and npm installed

### Step 1: Start the FastAPI Backend
```bash
# In Terminal 1 (from repository root):
python -m pip install -r requirements.txt
python -m uvicorn Backend.main:app --reload --port 8000
```
Backend will be live at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

### Step 2: Start the React Frontend Dev Server
```bash
# In Terminal 2 (from repository root):
cd Frontend
npm install
npm run dev
```
Frontend will be live at `http://localhost:5173`.

### Step 3: View the Amazon Clone Shopping Frontend
Open `http://127.0.0.1:8000/amazon` or `amazon clone/Amazon.html` in your browser.

### Step 4: Run the Complete Automated Test Suite
```bash
python run_all_tests.py
```
This executes all 10 project verification suites across Worker, Auditor, Database, API, and Frontend builds.

---

## 6. Live Application Testing & Verification Checklist

Once deployed online, complete the following verification steps on your public URL:

- [ ] **1. Frontend Loads Cleanly**: Navigate to your public frontend URL (e.g., `https://safecart.vercel.app`). Verify headers, logos, info cards, form, and sidebar render with zero layout shift.
- [ ] **2. Responsive Viewport Check**:
  - Test on **Desktop** (1920x1080 and 1366x768): 2-column layout (main content + sidebar).
  - Test on **Tablet** (768px - 1024px): 1-column responsive flow, sidebar wraps cleanly below.
  - Test on **Mobile** (375px - 414px): Single-column, touch-friendly inputs (>=46px min-height), no horizontal scrollbar, clear readability.
  - Test on **Extra Small Mobile** (<=360px): Compact spacing, zero overlapping elements.
- [ ] **3. Backend Health Check**: Open `https://<YOUR-BACKEND>/health` -> should return `{"status": "healthy", "service": "SafeCart API"}`.
- [ ] **4. Interactive Docs**: Open `https://<YOUR-BACKEND>/docs` -> Swagger UI displays all endpoints (`/api/chat`, `/api/products`, `/api/orders`, `/api/checkout`, etc.).
- [ ] **5. Product Info & Verified Image Query**:
  - In Customer Form, enter Query: `"Tell me about this product"` and Product ID: `"P001"`.
  - Click **Ask SafeCart**.
  - Verify SafeCart responds with Auditor approval, detailed description, and renders a **Verified Product Card** displaying the matched headphones photograph (`/product_images/P001.jpg`), category, price, and stock.
- [ ] **6. Compliance Guardrail Test (Refund Rejection)**:
  - Enter Query: `"Can I get a refund?"` and Order ID: `"O010"`.
  - Click **Ask SafeCart**.
  - Verify SafeCart status shows Auditor compliance check confirming Order O010 is not eligible for refund.
- [ ] **7. Price Verification & Correction**:
  - Enter Query: `"What is the price of this product?"` and Product ID: `"P002"`.
  - Verify response states verified database price of `Rs. 499`.
- [ ] **8. Amazon Clone E-Commerce Integration**:
  - Open `https://<YOUR-BACKEND>/amazon`.
  - Verify 500 catalog items display with correct archetype photographs, live stock badges, categories, and shopping cart functionality.
  - Open the SafeCart AI compliance chatbot drawer on the bottom right and ask a question.

---

## 7. Troubleshooting Common Issues

### Issue 1: "Cannot connect to the SafeCart backend" error in frontend
- **Cause**: `VITE_API_BASE_URL` is either missing, pointing to `localhost`, or has an invalid URL.
- **Fix**: In Vercel or Netlify dashboard, go to **Settings** > **Environment Variables**. Set `VITE_API_BASE_URL` to `https://<your-backend-app>.onrender.com/api`. Redeploy the frontend.

### Issue 2: Render Free Tier "Cold Start" delay (takes 30-50 seconds on first request)
- **Cause**: Free tier web services on Render spin down after 15 minutes of inactivity.
- **Fix**: The first request wakes the container. Subsequent requests respond instantly. If you need 100% uptime without sleep, upgrade to Render Starter or set up a free uptime monitor (e.g., UptimeRobot) pinging `/health` every 10 minutes.

### Issue 3: CORS Error in Browser Console (`Access-Control-Allow-Origin`)
- **Cause**: Backend does not allow the frontend origin.
- **Fix**: Ensure `ALLOWED_ORIGINS` is set to `*` in the backend environment variables on Render. Our updated backend also automatically matches any `*.vercel.app` and `*.netlify.app` domain.

### Issue 4: Mixed Content Warning (`Blocked loading mixed active content`)
- **Cause**: Frontend is loaded over HTTPS, but trying to query an HTTP backend.
- **Fix**: Always use `https://` for both frontend and backend URLs in production.

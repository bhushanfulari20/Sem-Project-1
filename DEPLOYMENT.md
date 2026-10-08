# 🚀 SafeCart Deployment Guide

SafeCart can be deployed in multiple ways depending on your needs. Below are the 4 recommended deployment options, ranging from completely free 1-click cloud platforms to Docker and separated frontend/backend deployments.

---

## 📋 Table of Contents
1. [Option 1: 100% Free All-in-One Web Service on Render (Recommended)](#option-1-render-all-in-one-free)
2. [Option 2: Separated Production Deployment (Vercel + Render)](#option-2-separated-deployment-vercel--render)
3. [Option 3: Docker & Docker Compose (Any Cloud / VPS / Local)](#option-3-docker--docker-compose)
4. [Option 4: Instant Public Demo via Cloudflare Tunnel / Ngrok (Zero Cost)](#option-4-instant-public-demo)
5. [Environment Variables Reference](#environment-variables-reference)
6. [Post-Deployment Verification Checklist](#post-deployment-verification-checklist)

---

## Option 1: Render All-in-One Free (Recommended)

Render offers a free tier where your entire SafeCart app (React Frontend + FastAPI Backend + CSV Database) runs together on a single public URL.

### Method A: Using Docker on Render (Easiest & Most Reliable)
1. Push your repository to **GitHub**.
2. Log in to [Render.com](https://render.com).
3. Click **New +** > **Web Service**.
4. Connect your GitHub repository `Sem-Project-1-main`.
5. Configure the service:
   - **Name**: `safecart` (or your preferred name)
   - **Region**: Choose the closest region (e.g., Singapore, Frankfurt, Oregon)
   - **Environment**: **Docker**
   - **Plan Type**: **Free**
6. Click **Deploy Web Service**.
7. Render will automatically build the React frontend with Node.js and package the FastAPI backend using our provided `Dockerfile`.
8. Once deployed, open your Render URL (e.g. `https://safecart.onrender.com`). You will see the complete SafeCart web application!

### Method B: Using Native Python Runtime on Render
If you prefer not to use Docker:
- **Build Command**:
  ```bash
  pip install -r requirements.txt && cd Frontend && npm install && npm run build && cd ..
  ```
- **Start Command**:
  ```bash
  uvicorn Backend.main:app --host 0.0.0.0 --port $PORT
  ```

---

## Option 2: Separated Deployment (Vercel + Render)

In this architecture:
- **FastAPI Backend** is hosted on **Render** (or Railway / Fly.io / Koyeb).
- **React Frontend** is hosted globally on **Vercel** CDN (blazing fast).

### Step 1: Deploy Backend to Render
1. Create a **New Web Service** on Render connected to your GitHub repo.
2. Select **Python** runtime:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn Backend.main:app --host 0.0.0.0 --port $PORT`
3. In **Environment Variables**, add:
   - `ALLOWED_ORIGINS`: `*` (or your future Vercel domain)
4. Deploy and copy your backend URL, for example: `https://safecart-api.onrender.com`.
5. Verify it's working: visit `https://safecart-api.onrender.com/health` in your browser.

### Step 2: Deploy Frontend to Vercel
1. Log in to [Vercel](https://vercel.com) and click **Add New...** > **Project**.
2. Import your GitHub repository.
3. In the project settings:
   - **Root Directory**: `Frontend`
   - **Framework Preset**: `Vite`
4. Expand **Environment Variables** and add:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://safecart-api.onrender.com/api` *(replace with your actual Render backend URL)*
5. Click **Deploy**.
6. Vercel will give you a public URL (e.g., `https://safecart.vercel.app`) that queries your live backend API!

---

## Option 3: Docker & Docker Compose

Deploy on any Linux server, VPS (DigitalOcean, Linode, AWS EC2, GCP Compute Engine), or container service (AWS ECS, Google Cloud Run).

### Run with Docker:
```bash
# 1. Build the production image
docker build -t safecart:latest .

# 2. Run container on port 8000
docker run -d -p 8000:8000 --name safecart safecart:latest
```
Visit `http://localhost:8000` (or `http://YOUR_SERVER_IP:8000`).

### Run with Docker Compose:
```bash
docker compose up -d --build
```
To stop the application:
```bash
docker compose down
```

### Deploy to Google Cloud Run (Serverless Container):
```bash
# Authenticate and deploy directly from source
gcloud run deploy safecart \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Option 4: Instant Public Demo (Zero Setup Cloudflare Tunnel)

If you have a live demo or presentation right now and want to make your local running app accessible to anyone on the internet for free without signing up for cloud hosting:

1. Start SafeCart unified server locally:
   ```bash
   cd Frontend
   npm run build
   cd ..
   python -m uvicorn Backend.main:app --host 0.0.0.0 --port 8000
   ```
2. In another terminal, download and run Cloudflare Tunnel (no account required):
   ```bash
   # On Windows (using winget or cloudflared executable):
   winget install --id Cloudflare.cloudflared
   cloudflared tunnel --url http://localhost:8000
   ```
3. Cloudflare gives you a temporary free HTTPS link (e.g. `https://random-words.trycloudflare.com`) accessible from any phone or computer worldwide!

---

## ⚙️ Environment Variables Reference

| Variable | Default Value | Description |
|---|---|---|
| `PORT` | `8000` | Port for Uvicorn HTTP server to listen on. Automatically set by Render/Railway/Heroku. |
| `ALLOWED_ORIGINS` | `*` | Comma-separated list of allowed CORS origins (e.g. `https://safecart.vercel.app,http://localhost:5173`). Set to `*` to allow all. |
| `VITE_API_BASE_URL` | `/api` | Frontend API base URL. Use `/api` for unified hosting, or `https://backend-domain.com/api` for separate frontend hosting. |

---

## ✅ Post-Deployment Verification Checklist

Once deployed, test these endpoints on your live domain:
- [ ] **Frontend Home Page**: Open `https://<YOUR-DOMAIN>/` and verify the SafeCart UI loads cleanly.
- [ ] **Health Check**: Open `https://<YOUR-DOMAIN>/health` -> should return `{"status": "healthy", "service": "SafeCart API"}`.
- [ ] **Interactive API Docs**: Open `https://<YOUR-DOMAIN>/docs` -> Swagger UI should be accessible.
- [ ] **Live Price Query**: Enter product query *"What is the price of this product?"* with Product ID `P001` -> should respond with verified price `Rs. 1999`.
- [ ] **Compliance Guardrail Test**: Enter *"Can I get a refund?"* with Order ID `O010` -> Auditor Agent should block refund and confirm non-refundable status.

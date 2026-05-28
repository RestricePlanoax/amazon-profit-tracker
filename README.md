# Amazon Seller Profit Tracker

Amazon Seller Profit Tracker is a CSV-first SaaS MVP for sellers who want to see true profit by day and by SKU instead of relying on topline Amazon revenue alone.

The app lets a seller:

- sign up with email and password
- upload Amazon orders and ads CSV files
- upload settlement reports and bulk COGS CSV files
- prevent duplicate imports with file hashes and row-level dedupe
- delete or reprocess an import batch safely
- load a demo store when a prospect wants to see value immediately
- process uploads in the background
- view calendar-based revenue, net profit, margin, TACOS, ACOS, and refund rate
- compare the selected period against the previous equivalent period
- switch between financial and efficiency line charts
- render dashboard/onboarding metrics from a backend metric catalog
- review rule-based seller insights with an LLM-ready recommendation scaffold
- review SKU-level profitability and update COGS per SKU

## Tech Stack

- Frontend: Next.js App Router, TypeScript, Tailwind CSS, shadcn-style UI primitives, Recharts
- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Auth: JWT
- Upload storage: local filesystem
- Background work: FastAPI `BackgroundTasks`
- Deployment: Docker Compose locally, Vercel Services for hosted MVP

## Repo Structure

```text
amazon-profit-tracker/
  frontend/
  backend/
  docker-compose.yml
  vercel.json
  sample_orders.csv
  sample_ads.csv
  sample_settlements.csv
  sample_inventory.csv
  sample_cogs.csv
  README.md
```

## Quick Start With Docker

From the repo root:

```bash
docker compose up --build
```

Once the services are up:

- frontend: [http://localhost:3000](http://localhost:3000)
- backend API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- backend health check: [http://localhost:8000/health](http://localhost:8000/health)

## Local Development Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

## Environment Variables

### Backend

- `DATABASE_URL`
- `JWT_SECRET`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `UPLOAD_DIR`
- `CORS_ORIGINS`

Example values are included in [backend/.env.example](/Users/vishnu/Desktop/amazon-profit-tracker/backend/.env.example).

### Frontend

- `NEXT_PUBLIC_API_BASE_URL`

Example values are included in [frontend/.env.local.example](/Users/vishnu/Desktop/amazon-profit-tracker/frontend/.env.local.example).

## Deploy On Vercel

This repo uses Vercel Services so the Next.js frontend and FastAPI backend deploy from the same GitHub repo and share one domain.

1. Import the GitHub repo in Vercel.
2. Choose the `Services` application preset.
3. Vercel should read [vercel.json](/Users/vishnu/Desktop/personals/amazon-profit-tracker/vercel.json) and detect:
   - `frontend`: Next.js at `/`
   - `backend`: FastAPI at `/api`
4. Add environment variables in Vercel Project Settings:
   - `DATABASE_URL`: production PostgreSQL URL from Neon, Supabase, Vercel Postgres, or another managed Postgres provider.
   - `JWT_SECRET`: a long random secret.
   - `ACCESS_TOKEN_EXPIRE_MINUTES`: `1440`
   - `UPLOAD_DIR`: `/tmp/uploads`
   - `CORS_ORIGINS`: your Vercel production URL, for example `https://amazon-profit-tracker.vercel.app`
5. Deploy.
6. Run migrations against the production database from your machine:

```bash
cd backend
source .venv/bin/activate
DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:PORT/DB?sslmode=require" alembic upgrade head
```

Notes:

- The frontend reads Vercel's generated `NEXT_PUBLIC_BACKEND_URL` automatically, so you usually do not need to set `NEXT_PUBLIC_API_BASE_URL` on Vercel.
- Local CSV upload storage is ephemeral on Vercel serverless. It is acceptable for a quick demo, but before selling paid plans, move uploads to durable storage such as Vercel Blob, S3, or Cloudflare R2.
- BackgroundTasks can run for short MVP jobs, but larger Amazon report processing should move to a durable queue/worker later.

## Sample CSV Files

Root-level sample files are included so you can sign up and test the MVP quickly:

- [sample_orders.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_orders.csv)
- [sample_ads.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_ads.csv)
- [sample_settlements.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_settlements.csv)
- [sample_cogs.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_cogs.csv)

These demo files now cover a longer date range from `2024-01-01` onward so the dashboard can show meaningful calendar-based trends and period-over-period change.

### Orders CSV

```csv
order_date,order_id,sku,units,revenue,fees,refund
2026-04-01,ORD001,SKU-001,2,2000,300,0
2026-04-01,ORD002,SKU-002,1,1500,225,0
2026-04-02,ORD003,SKU-001,1,1000,150,100
```

### Ads CSV

```csv
date,sku,spend,sales,clicks,impressions
2026-04-01,SKU-001,300,2000,20,1000
2026-04-01,SKU-002,200,1500,15,800
2026-04-02,SKU-001,150,1000,10,500
```

### Settlement CSV

```csv
settlement_date,settlement_id,total_amount,fees,taxes,reimbursements
2026-04-01,SET001,12000,1400,240,100
2026-04-15,SET002,18500,2200,370,0
```

### Bulk COGS CSV

```csv
sku,name,cogs
SKU-001,Demo Bottle,420
SKU-002,Demo Organizer,310
```

## MVP Notes

- Signup automatically creates one default store for the user.
- Uploads are saved to `backend/storage/uploads`.
- CSV parsing is tolerant of header case, spaces, common Amazon-style names, and common delimiters.
- Upload failures store the validation reason on the upload record.
- Daily metrics are recomputed after each successful upload or COGS update.
- Upload file hashes prevent the exact same file from being imported twice.
- Import batches track inserted/skipped row counts and support delete/reprocess actions.
- Row hashes make ingestion idempotent for orders, ads, settlements, and demo rows.
- Demo mode seeds a realistic 180-day store so the dashboard is useful before a seller has exports ready.

## Profit Formula

For each SKU and day:

```text
gross_revenue = sum(order revenue)
fees = sum(order fees)
refund = sum(order refund)
ad_spend = sum(ad spend)
cogs = product.cogs * units_sold
net_profit = revenue - fees - taxes - refund - ad_spend - cogs + reimbursements
profit_margin = net_profit / revenue * 100
```

## API Overview

### Auth

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`

### Uploads

- `POST /uploads/orders`
- `POST /uploads/ads`
- `POST /uploads/settlement`
- `GET /uploads`
- `DELETE /uploads/{upload_id}`
- `POST /uploads/{upload_id}/reprocess`

### Dashboard

- `GET /dashboard/date-bounds`
- `GET /dashboard/summary?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- `GET /dashboard/trends?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- `GET /dashboard/insights?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

### Demo And Metrics

- `POST /demo/load`
- `GET /metrics/catalog`

### Products

- `GET /products/profitability?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- `PUT /products/{sku}/cogs`
- `POST /products/cogs/bulk`

## Seed / Sample Flow

1. Start the stack.
2. Create a new account from the landing page.
3. Open the Uploads page.
4. Upload [sample_orders.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_orders.csv).
5. Upload [sample_ads.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_ads.csv).
6. Optionally upload [sample_settlements.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_settlements.csv).
7. Optionally upload [sample_cogs.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_cogs.csv) from the Products page.
8. Open Dashboard and Products to verify daily and SKU-level profit metrics.

For a faster prospect demo, create an account and click **Load demo store** on the dashboard.

If you want to regenerate the demo CSVs:

```bash
cd backend
source .venv/bin/activate
python scripts/generate_demo_csvs.py
```

## Next Roadmap

- Add real Amazon SP-API OAuth and seller authorization
- Pull reports from the Amazon Reports API into the same import batch pipeline
- Add inventory CSV processing and stockout/sell-through analytics
- Add multi-store support per user
- Add scheduled report sync jobs and audit logs

## Notes On Future Amazon SP-API Integration

The backend is intentionally split into upload parsing, worker processing, and metrics aggregation layers so CSV ingestion can later be swapped with a direct Amazon Reports API sync flow without redesigning the profitability model.

## References

- [Next.js App Router docs](https://nextjs.org/docs/app)
- [FastAPI SQL databases tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [Alembic documentation](https://alembic.sqlalchemy.org/en/latest/)
- [Amazon SP-API Reports API](https://developer-docs.amazon.com/sp-api/docs/reports-api)

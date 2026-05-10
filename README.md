# Amazon Seller Profit Tracker

Amazon Seller Profit Tracker is a CSV-first SaaS MVP for sellers who want to see true profit by day and by SKU instead of relying on topline Amazon revenue alone.

The app lets a seller:

- sign up with email and password
- upload Amazon orders and ads CSV files
- process uploads in the background
- view calendar-based revenue, net profit, margin, TACOS, ACOS, and refund rate
- compare the selected period against the previous equivalent period
- switch between financial and efficiency line charts
- review rule-based seller insights with an LLM-ready recommendation scaffold
- review SKU-level profitability and update COGS per SKU

## Tech Stack

- Frontend: Next.js App Router, TypeScript, Tailwind CSS, shadcn-style UI primitives, Recharts
- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Auth: JWT
- Upload storage: local filesystem
- Background work: FastAPI `BackgroundTasks`
- Deployment: Docker Compose

## Repo Structure

```text
amazon-profit-tracker/
  frontend/
  backend/
  docker-compose.yml
  sample_orders.csv
  sample_ads.csv
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

## Sample CSV Files

Root-level sample files are included so you can sign up and test the MVP quickly:

- [sample_orders.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_orders.csv)
- [sample_ads.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_ads.csv)

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

## MVP Notes

- Signup automatically creates one default store for the user.
- Uploads are saved to `backend/storage/uploads`.
- CSV parsing is tolerant of header case and spaces. Headers are trimmed, lowercased, and spaces are converted to underscores.
- Upload failures store the validation reason on the upload record.
- Daily metrics are recomputed after each successful upload or COGS update.
- The current MVP is additive. Re-uploading the same report will insert duplicate data unless you clear it manually.

## Profit Formula

For each SKU and day:

```text
gross_revenue = sum(order revenue)
fees = sum(order fees)
refund = sum(order refund)
ad_spend = sum(ad spend)
cogs = product.cogs * units_sold
net_profit = revenue - fees - refund - ad_spend - cogs
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
- `GET /uploads`

### Dashboard

- `GET /dashboard/summary?range=30d`
- `GET /dashboard/trends?range=30d`

### Products

- `GET /products/profitability?range=30d`
- `PUT /products/{sku}/cogs`

## Seed / Sample Flow

1. Start the stack.
2. Create a new account from the landing page.
3. Open the Uploads page.
4. Upload [sample_orders.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_orders.csv).
5. Upload [sample_ads.csv](/Users/vishnu/Desktop/amazon-profit-tracker/sample_ads.csv).
6. Open Dashboard and Products to verify daily and SKU-level profit metrics.

If you want to regenerate the demo CSVs:

```bash
cd backend
source .venv/bin/activate
python scripts/generate_demo_csvs.py
```

## Next Roadmap

- Add Amazon SP-API seller authorization
- Pull reports from the Amazon Reports API instead of manual-only CSV uploads
- Support settlement report ingestion
- Add duplicate detection and idempotent imports
- Add multi-store support per user
- Add scheduled report sync jobs and audit logs

## Notes On Future Amazon SP-API Integration

The backend is intentionally split into upload parsing, worker processing, and metrics aggregation layers so CSV ingestion can later be swapped with a direct Amazon Reports API sync flow without redesigning the profitability model.

## References

- [Next.js App Router docs](https://nextjs.org/docs/app)
- [FastAPI SQL databases tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [Alembic documentation](https://alembic.sqlalchemy.org/en/latest/)
- [Amazon SP-API Reports API](https://developer-docs.amazon.com/sp-api/docs/reports-api)

# Inventory & Order Management System

A production-ready full-stack inventory and order management system with:

- FastAPI backend
- React frontend
- PostgreSQL database
- Docker and Docker Compose
- Deployment-ready configuration for free hosting platforms

## Features

- Product management: create, list, view, update, delete
- Customer management: create, list, view, delete
- Order management: create, list, view, delete with automatic stock reduction
- Dashboard summary with low-stock products
- Validation, uniqueness checks, and proper HTTP status codes

## Project structure

```text
inventory-order-app/
  backend/
  frontend/
  docker-compose.yml
```

## Local development with Docker

1. Copy environment files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. Start the app:

```bash
docker compose up --build
```

3. Open:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs
- PostgreSQL: localhost:5432

## Environment variables

### Backend

- `DATABASE_URL`
- `FRONTEND_ORIGIN`
- `LOW_STOCK_THRESHOLD`

### Frontend

- `VITE_API_BASE_URL`

## Deployment

### Backend
Deploy the backend on Render, Railway, or Fly.io.

Environment variables to set:

- `DATABASE_URL`
- `FRONTEND_ORIGIN`
- `LOW_STOCK_THRESHOLD`

### Frontend
Deploy the frontend on Vercel or Netlify.

Environment variables to set:

- `VITE_API_BASE_URL`

Point `VITE_API_BASE_URL` to the deployed backend URL.

## API endpoints

### Products
- `POST /products`
- `GET /products`
- `GET /products/{id}`
- `PUT /products/{id}`
- `DELETE /products/{id}`

### Customers
- `POST /customers`
- `GET /customers`
- `GET /customers/{id}`
- `DELETE /customers/{id}`

### Orders
- `POST /orders`
- `GET /orders`
- `GET /orders/{id}`
- `DELETE /orders/{id}`

### Dashboard
- `GET /dashboard/summary`

## Notes

- Order deletion restores inventory.
- SKU and email fields are unique.
- Inventory cannot go negative.
- All data is validated before database writes.

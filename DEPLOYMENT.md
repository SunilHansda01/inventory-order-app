# Deployment Guide

## Backend (Render, Railway, or Fly.io)

Set these environment variables:

- `DATABASE_URL`
- `FRONTEND_ORIGIN`
- `LOW_STOCK_THRESHOLD`

Use the backend Dockerfile in `backend/Dockerfile`.

## Frontend (Vercel or Netlify)

Set:

- `VITE_API_BASE_URL`

Point it to the deployed backend URL.

The frontend Dockerfile is included for local Docker use. For Vercel/Netlify, deploy the `frontend` folder as a static app.

## Local Docker

```bash
docker compose up --build
```

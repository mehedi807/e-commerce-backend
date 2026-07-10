# Environment Configuration Reference

This document describes how to configure the local environment parameters for the E-Commerce Order and Payment System using `.env`.

## Setup

1. Copy `.env.example` to `.env` in the project root:
   ```bash
   cp .env.example .env
   ```
2. Configure the variables inside `.env` according to the tables below.

---

## Configuration Reference

### Django settings
* **`DEBUG`** (Bool): Toggle Django debug mode.
* **`SECRET_KEY`** (Str): Django cryptographic signing key.
* **`ALLOWED_HOSTS`** (List): comma-separated hosts allowed to serve the app (e.g. `*` or `localhost`).
* **`CORS_ALLOW_ALL_ORIGINS`** (Bool): Toggles CORS checks on requests (`True` for local frontend testing).

### Database & Cache
* **`POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`** (Str): Database credentials.
* **`REDIS_URL`** (Str): Redis connection URI (e.g. `redis://redis:6379/0`).

### Stripe Integration
* **`STRIPE_SECRET_KEY`** (Str): Secret key for Stripe API endpoints (e.g. `sk_test_...`).
* **`STRIPE_PUBLISHABLE_KEY`** (Str): Publishable key used in Stripe Checkout (e.g. `pk_test_...`).
* **`STRIPE_WEBHOOK_SECRET`** (Str): Secret signature verifier for Stripe webhook callbacks.
* **`STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL`** (Str): Frontend redirect URLs.

### bKash Integration
* **`BKASH_APP_KEY` / `BKASH_APP_SECRET`** (Str): Sandbox credentials.
* **`BKASH_USERNAME` / `BKASH_PASSWORD`** (Str): Sandbox API merchant login credentials.
* **`BKASH_BASE_URL`** (Str): Target gateway (e.g. `https://checkout.sandbox.bka.sh/v1.2.0-beta`).
* **`BKASH_CALLBACK_URL`** (Str): Ingress webhook callback URL (e.g. `https://<ngrok-domain>/api/payments/bkash/callback`).
* **`BKASH_FRONTEND_REDIRECT_URL`** (Str): Redirect target after checkout completion.

### Ngrok Tunnel
* **`NGROK_AUTHTOKEN`** (Str): Authentication token from your ngrok dashboard.
* **`NGROK_DOMAIN`** (Str): Claimed ngrok static domain mapped to the project tunnel.

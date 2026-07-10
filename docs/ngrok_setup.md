# Local Ngrok Setup

This document describes how to run and test the local containerized ngrok tunnel.

---

## 1. Running the Tunnel (Docker Compose)

The ngrok tunnel service is configured inside [docker-compose.dev.yml](file:///home/mehedi/Git/Home/e-commerce-backend/docker-compose.dev.yml). To launch it alongside the backend application:

```bash
# Start all development services, including ngrok
docker compose -f docker-compose.dev.yml up -d

# Verify ngrok is running
docker compose -f docker-compose.dev.yml ps ngrok

# View live tunnel connection status and logs
docker compose -f docker-compose.dev.yml logs ngrok
```

---

## 2. Active Testing Credentials

The following working development credentials and domain are pre-configured in `.env` for testing:

* **Authtoken**: `3EcQ4wQFvhY8fYHMVI1Qrrbmg1s_uyMzjzHbZXyTSU7sQWvd`
* **Static Domain**: `outspoken-detract-semisoft.ngrok-free.dev`

---

## 3. Inspecting Tunnel Traffic

To monitor incoming webhooks or view HTTP payloads, open the local ngrok inspection dashboard in web browser:

**Local Dashboard URL**: **[http://localhost:4040](http://localhost:4040)**

---

## 4. Configuring a Custom Personal Tunnel

To replace the pre-configured credentials:

1. Sign up at [ngrok.com](https://ngrok.com) and retrieve **Authtoken** from the dashboard.
2. Get the free static domain.
3. Update the `.env` values:
   ```env
   NGROK_AUTHTOKEN=your_personal_authtoken
   NGROK_DOMAIN=your-domain.ngrok-free.app
   ```
4. Recreate the containers:
   ```bash
   docker compose -f docker-compose.dev.yml down && docker compose -f docker-compose.dev.yml up -d
   ```

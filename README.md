# InnKeeper Pro — Setup & Run Guide

## What's Included

```
innkeeper/
├── app.py          ← Flask backend (REST API + SQLite DB)
├── start.sh        ← One-command server launcher
├── stop.sh         ← Stop the server
├── requirements.txt
├── innkeeper.db    ← Auto-created SQLite database
└── static/
    └── index.html  ← Full frontend SPA (served by Flask)
```

---

## Quick Start (any Linux/Mac machine with Python 3.8+)

### Step 1 — Install dependencies

```bash
pip install flask
```
> Flask is the only dependency. SQLite3 comes built into Python.

### Step 2 — Start the server

```bash
cd innkeeper
bash start.sh
```

You'll see:
```
✅ Server running (PID: 12345)

🌐 Open this URL in your browser:
   ➜  http://192.168.1.x:8080
   ➜  http://localhost:8080
```

### Step 3 — Open your browser

Go to: **http://localhost:8080**

The app loads with demo data (5 guests, 30 rooms, sample bookings).

---

## Run on Your Internal Network (LAN)

Any device on your **same Wi-Fi/network** can access it:

1. Find your machine's local IP:
   ```bash
   hostname -I        # Linux
   ipconfig           # Windows
   ifconfig en0       # Mac
   ```

2. Share the URL with colleagues:
   ```
   http://192.168.x.x:8080
   ```

3. Multiple staff can use it simultaneously — Flask runs multi-threaded.

---

## Stop the Server

```bash
bash stop.sh
```

---

## REST API Endpoints

All endpoints return JSON `{ "ok": true, "data": ... }`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Stats, celebrations, recent bookings |
| GET/POST | `/api/guests` | List or create guests |
| GET/PUT | `/api/guests/:id` | Get or update a guest |
| GET/POST | `/api/rooms` | List rooms (filter by status/type) |
| PATCH | `/api/rooms/:id` | Update room status |
| GET/POST | `/api/bookings` | List or create bookings |
| PATCH | `/api/bookings/:id` | Update booking |
| POST | `/api/bookings/:id/checkin` | Check a guest in |
| POST | `/api/bookings/:id/checkout` | Check a guest out + generate receipt |
| GET/POST | `/api/payments` | Record payments |
| GET/POST | `/api/receipts` | List or generate receipts |
| GET | `/api/receipts/:id` | Full receipt detail |
| GET | `/api/celebrations` | Birthdays & anniversaries |
| POST | `/api/celebrations/send` | Log a wish sent |
| GET | `/api/reports/summary` | Revenue, occupancy, analytics |
| GET/POST | `/api/settings` | Read or update hotel settings |
| GET | `/api/health` | Server health check |

---

## Database

SQLite database auto-created at `innkeeper/innkeeper.db`.  
To reset to fresh demo data: `rm innkeeper.db` then restart.

To back up: `cp innkeeper.db innkeeper_backup_$(date +%Y%m%d).db`

---

## Production Deployment

For a real deployment, replace Flask dev server with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

Or use systemd to run it as a service (see below).

### systemd service (Linux servers)

Create `/etc/systemd/system/innkeeper.service`:
```ini
[Unit]
Description=InnKeeper Pro Hotel Management
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/innkeeper
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
systemctl enable innkeeper
systemctl start innkeeper
```

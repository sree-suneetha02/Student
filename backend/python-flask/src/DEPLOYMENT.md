# Deployment Guide — Cloud VM (Ubuntu)

Deploy all 3 backends to a Linux Ubuntu VM on any cloud provider.
(AWS EC2 / GCP Compute Engine / Azure VM / DigitalOcean Droplet)

---

## Architecture

```
Internet
   │
   ▼
Nginx (port 80/443)  ← reverse proxy
   │
   ├── /api/python  →  Flask   (port 5015)
   ├── /api/nodejs  →  Express (port 5016)
   └── /api/golang  →  Gin     (port 5017)
```

---

## Step 1 — Create the VM

### Minimum Requirements
| Resource | Minimum |
|----------|---------|
| OS | Ubuntu 22.04 LTS |
| RAM | 1 GB |
| CPU | 1 vCPU |
| Storage | 10 GB |
| Ports open | 22 (SSH), 80 (HTTP), 443 (HTTPS) |

### Open Firewall Ports
On your cloud provider dashboard, open inbound ports:
- `22` — SSH
- `80` — HTTP
- `443` — HTTPS

---

## Step 2 — Connect to the VM

```bash
ssh ubuntu@YOUR_VM_IP
# or
ssh -i your-key.pem ubuntu@YOUR_VM_IP
```

---

## Step 3 — Update the Server

```bash
sudo apt update && sudo apt upgrade -y
```

---

## Step 4 — Install Dependencies

### Install Python

```bash
sudo apt install -y python3 python3-pip python3-venv
python3 --version
```

### Install Node.js

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version
```

### Install Go

```bash
wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
go version
```

### Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Install Git

```bash
sudo apt install -y git
```

---

## Step 5 — Clone the Repository

```bash
cd /home/ubuntu
git clone https://github.com/sree-suneetha02/Student.git
cd Student
```

---

## Step 6 — Setup Python (Flask) Backend

```bash
cd /home/ubuntu/Student/backend/python-flask/src/python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r ../requirements.txt

# Test it runs
python3 app.py
# Press Ctrl+C to stop
```

### Create systemd service for Python

```bash
sudo nano /etc/systemd/system/student-python.service
```

Paste this content:

```ini
[Unit]
Description=Student API - Python Flask
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Student/backend/python-flask/src/python
Environment="PATH=/home/ubuntu/Student/backend/python-flask/src/python/venv/bin"
ExecStart=/home/ubuntu/Student/backend/python-flask/src/python/venv/bin/python3 app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X` → `Y` → `Enter`

```bash
sudo systemctl daemon-reload
sudo systemctl start student-python
sudo systemctl enable student-python
sudo systemctl status student-python
```

---

## Step 7 — Setup Node.js (Express) Backend

```bash
cd /home/ubuntu/Student/backend/python-flask/src/nodejs
npm install

# Test it runs
node app.js
# Press Ctrl+C to stop
```

### Create systemd service for Node.js

```bash
sudo nano /etc/systemd/system/student-nodejs.service
```

Paste this content:

```ini
[Unit]
Description=Student API - Node.js Express
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Student/backend/python-flask/src/nodejs
ExecStart=/usr/bin/node app.js
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X` → `Y` → `Enter`

```bash
sudo systemctl daemon-reload
sudo systemctl start student-nodejs
sudo systemctl enable student-nodejs
sudo systemctl status student-nodejs
```

---

## Step 8 — Setup Go (Gin) Backend

```bash
cd /home/ubuntu/Student/backend/python-flask/src/golang
go mod tidy

# Build binary
go build -o student-api .

# Test it runs
./student-api
# Press Ctrl+C to stop
```

### Create systemd service for Go

```bash
sudo nano /etc/systemd/system/student-golang.service
```

Paste this content:

```ini
[Unit]
Description=Student API - Go Gin
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Student/backend/python-flask/src/golang
ExecStart=/home/ubuntu/Student/backend/python-flask/src/golang/student-api
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Save: `Ctrl+X` → `Y` → `Enter`

```bash
sudo systemctl daemon-reload
sudo systemctl start student-golang
sudo systemctl enable student-golang
sudo systemctl status student-golang
```

---

## Step 9 — Check All 3 Services Running

```bash
sudo systemctl status student-python
sudo systemctl status student-nodejs
sudo systemctl status student-golang
```

All 3 should show: `Active: active (running)`

### Quick health check

```bash
curl http://localhost:5015/health   # Python
curl http://localhost:5016/health   # Node.js
curl http://localhost:5017/health   # Go
```

---

## Step 10 — Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/student-api
```

Paste this content:

```nginx
server {
    listen 80;
    server_name codekaryashala.com www.codekaryashala.com;

    # Python Flask — port 5015
    location /api/python/ {
        proxy_pass http://localhost:5015/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Node.js Express — port 5016
    location /api/nodejs/ {
        proxy_pass http://localhost:5016/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Go Gin — port 5017
    location /api/golang/ {
        proxy_pass http://localhost:5017/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Save: `Ctrl+X` → `Y` → `Enter`

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/student-api /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## Step 11 — Point Domain to VM

In your domain registrar (where you manage codekaryashala.com):

Add an **A Record**:
```
Type:  A
Name:  @  (or codekaryashala.com)
Value: YOUR_VM_IP
TTL:   300
```

Wait 5–10 minutes for DNS to propagate.

Test:
```bash
curl http://codekaryashala.com/api/python/health
curl http://codekaryashala.com/api/nodejs/health
curl http://codekaryashala.com/api/golang/health
```

---

## Step 12 — Add HTTPS (SSL) with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx

sudo certbot --nginx -d codekaryashala.com -d www.codekaryashala.com
```

Follow the prompts — certbot will automatically update your nginx config.

Test HTTPS:
```bash
curl https://codekaryashala.com/api/python/health
curl https://codekaryashala.com/api/nodejs/health
curl https://codekaryashala.com/api/golang/health
```

Auto-renew SSL (runs twice a day):
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Step 13 — Test All Endpoints Live

```bash
BASE="https://codekaryashala.com"

# Health checks
curl $BASE/api/python/health
curl $BASE/api/nodejs/health
curl $BASE/api/golang/health

# Create student (Python)
curl -X POST $BASE/api/python/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","age":22,"email":"alice@example.com"}'

# Get all students (Node.js)
curl $BASE/api/nodejs/students

# Create student (Go)
curl -X POST $BASE/api/golang/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob","age":25,"email":"bob@example.com"}'
```

---

## Useful Commands After Deployment

### View logs

```bash
# Python logs
sudo journalctl -u student-python -f

# Node.js logs
sudo journalctl -u student-nodejs -f

# Go logs
sudo journalctl -u student-golang -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart a service

```bash
sudo systemctl restart student-python
sudo systemctl restart student-nodejs
sudo systemctl restart student-golang
```

### Stop a service

```bash
sudo systemctl stop student-python
```

### Deploy new code (update)

```bash
cd /home/ubuntu/Student
git pull origin main

# Restart affected services
sudo systemctl restart student-python
sudo systemctl restart student-nodejs

# For Go — rebuild binary first
cd backend/python-flask/src/golang
go build -o student-api .
sudo systemctl restart student-golang
```

---

## Summary

| Backend | Internal Port | Public URL |
|---------|--------------|------------|
| Python (Flask) | 5015 | `https://codekaryashala.com/api/python/` |
| Node.js (Express) | 5016 | `https://codekaryashala.com/api/nodejs/` |
| Go (Gin) | 5017 | `https://codekaryashala.com/api/golang/` |

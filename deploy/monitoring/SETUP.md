# Monitoring Stack Setup

This directory contains a self-contained monitoring stack (Prometheus + Grafana + Loki) that runs alongside the rule-editor Docker services.

---

## Prerequisites

- Docker and Docker Compose installed
- The main rule-editor stack already running (`docker compose up -d` in the repo root)
- A Slack workspace where you have permission to add Incoming Webhooks

---

## 1. Configure environment variables

```bash
cp monitoring.env.example monitoring.env
```

Open `monitoring.env` and fill in the values:

| Variable | Required | Description |
|---|---|---|
| `GRAFANA_ADMIN_USER` | No | Grafana admin username (default: `admin`) |
| `GRAFANA_ADMIN_PASSWORD` | No | Grafana admin password (default: `admin`) |
| `SLACK_WEBHOOK_URL` | Yes (for alerts) | Incoming Webhook URL from Slack |
| `MONITOR_TARGET_NETWORK` | No | Docker network to monitor (default: `rule-editor_rule-editor`) |

> **Security:** `monitoring.env` is git-ignored. Never commit it or share the Slack webhook URL.

---

## 2. Create a Slack Incoming Webhook

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and open your workspace's app, or create a new one.
2. In the left menu: **Features → Incoming Webhooks** → toggle **Activate Incoming Webhooks** to On.
3. Click **Add New Webhook to Workspace**, select the `#git-alerts` channel (or any channel you want), and confirm.
4. Copy the webhook URL (format: `https://hooks.slack.com/services/T.../B.../...`).
5. Paste it as `SLACK_WEBHOOK_URL` in your `monitoring.env`.

---

## 3. Start the monitoring stack

```bash
cd deploy/monitoring
docker compose -f docker-compose.monitoring.yml --env-file monitoring.env up -d
```

Grafana will be available at [http://localhost:3000](http://localhost:3000).  
Log in with the admin credentials from `monitoring.env` (default: `admin` / `admin`).

---

## 4. Verify Slack alerts are connected

1. In Grafana, go to **Alerting → Contact points**.
2. You should see **"Slack git-alerts"** listed.
3. Click the **Test** button (paper-plane icon) next to it.
4. A test message should appear in your `#git-alerts` channel within a few seconds.

---

## 5. Configure which services trigger alerts

Services are grouped by severity in [`prometheus.yml`](prometheus.yml). To change a service's alert behaviour, move it between groups:

```yaml
# severity=critical  → fires after 1 min down
- targets:
    - https://rule-editor.nl/
    - http://auth-service:8001/health

# severity=warning   → fires after 3 min down
- targets:
    - http://flint-to-eflint:8000/health
    - http://mongo-api:8002/health
    - http://git-service:8103/health

# severity=excluded  → monitored in Grafana but never sends an alert
- targets: []
```

**Examples:**
- **Stop alerting on git-service:** Move `http://git-service:8103/health` from `warning` to `excluded`.
- **Make mongo-api a critical alert:** Move it from `warning` to `critical`.
- **Add a new service:** Add its URL to the appropriate severity group.

After editing `prometheus.yml`, restart Prometheus:

```bash
docker compose -f docker-compose.monitoring.yml --env-file monitoring.env restart prometheus
```

---

## 6. Adjust alert timeout durations

Timeouts control how long a service must be continuously down before a Slack alert is sent. Edit [`grafana/provisioning/alerting/service-alerts.yml`](grafana/provisioning/alerting/service-alerts.yml):

| Rule | `for` value | Change to... |
|---|---|---|
| Critical Service Down | `1m` | `2m` or `5m` to reduce false positives |
| Service Down (warning) | `3m` | `5m` or `10m` for noisy services during deployments |
| MongoDB Unreachable | `2m` | Increase if MongoDB restarts frequently |

The group `interval: 1m` sets how often rules are re-evaluated. Lowering it (e.g. `30s`) gives faster detection but increases load.

After editing, restart Grafana:

```bash
docker compose -f docker-compose.monitoring.yml --env-file monitoring.env restart grafana
```

---

## 7. Notification policy (repeat interval)

By default, Grafana re-sends a Slack alert every **1 hour** while the service stays down. To change this, edit [`grafana/provisioning/alerting/slack-contact-point.yml`](grafana/provisioning/alerting/slack-contact-point.yml):

```yaml
policies:
  - receiver: Slack git-alerts
    group_wait: 30s        # delay before first notification after alert fires
    group_interval: 5m     # delay before notifying about new alerts in the same group
    repeat_interval: 1h    # how often to re-notify while alert is still firing
```

---

## Stop the monitoring stack

```bash
docker compose -f docker-compose.monitoring.yml --env-file monitoring.env down
```

To also delete stored metrics and logs (irreversible):

```bash
docker compose -f docker-compose.monitoring.yml --env-file monitoring.env down -v
```

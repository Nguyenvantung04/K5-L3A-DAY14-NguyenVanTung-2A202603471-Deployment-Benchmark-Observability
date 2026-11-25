# Deployment Information

## Public URL
(Cập nhật sau khi deploy `06-lab-complete/` lên Railway/Render)

## Platform
Railway / Render

## Test Commands

```bash
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/health"
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/ready"
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H "Content-Type: application/json" -d '{"question": "Hello"}'
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H "Content-Type: application/json" -H "X-API-Key: $AGENT_API_KEY" -d '{"question": "Hello"}'
```

## Environment Variables Set
- `PORT`
- `ENVIRONMENT=production`
- `REDIS_URL`
- `AGENT_API_KEY`
- `RATE_LIMIT_PER_MINUTE=10`
- `DAILY_BUDGET_USD=1.0`
- `MONTHLY_BUDGET_USD=10.0`

## Screenshots
- `screenshots/dashboard.png`
- `screenshots/running.png`
- `screenshots/test.png`

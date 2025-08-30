## BAC Hunter Web UI Backend

- Start API:

```bash
python -m webapp.main
```

- Endpoints:
- GET /api/commands
- POST /api/commands/{name}/execute
- GET /api/runs/{id}
- GET /api/runs/{id}/logs
- WS /ws/runs/{id}
- GET /api/db/findings
- GET /api/db/targets
- GET /api/orchestrator/status
- POST /api/orchestrator/enqueue
# BAC Hunter Documentation

## Architecture Overview

- core: `Settings`, `HttpClient`, `SessionManager`, `RateLimiter`, `Storage`
- scanners: recon/test plugins (`plugins.recon.*`, `enhanced_graphql`)
- utils: helpers for URLs, jitter, normalization, dedup
- reporting: exporters and report generation
- ai_assistants: optional AI analysis (`intelligence/ai/*`)

## Design Goals

- Single responsibility modules
- Resilience and graceful degradation
- Async‑first where network heavy
- Extensible scanners via a stable base class


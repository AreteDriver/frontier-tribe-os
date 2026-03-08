# EVE Frontier World API Notes

Track what works and what doesn't as we discover it.

## Known Endpoints

| Endpoint | Status | Notes |
|----------|--------|-------|
| TBD | TBD | Verify during hackathon Day 1 |

## Auth Flow

- EVE Frontier auth mechanism: TBD (OAuth2 vs wallet-based)
- Verify at builder Discord #builder-general

## Static Data Fallback

If World API is unavailable, we load from `backend/data/blueprints.json`.
This contains placeholder blueprint/material data for UI development.

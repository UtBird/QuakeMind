# Backend API contract requirements

`ServiceContracts.kt` is the compile-time boundary; the active Android Hilt
network bindings use the real FastAPI-backed services in
`core/network/.../real/`. The former development-only `Dev*Service`
fixtures are not used for production data. See [Backend bağlantısı](BACKEND_INTEGRATION.md)
for implemented routes, local Android configuration, authentication, and retry semantics.
No production URL is assumed.

Required contracts:

- Authentication: phone/email, OTP, guest session, refresh/revoke, capabilities.
- Earthquakes: paged nearby list, official source timestamp and optional live stream.
- Incidents: create with idempotency key, update, track, verify, reject, assign.
- NLP: category/location/needs/urgency/confidence/human-review result.
- Damage: resumable upload, progress/cancel, analysis boxes/masks and model version.
- Roads/routes: versioned road segments and route alternatives with risk evidence.
- Risk: factors, data sources and update timestamp; never an earthquake prediction.
- Notifications: registration token, preferences, inbox, mark read and deep-link data.
- Safety: status update and explicit contact-delivery channel/result.
- Sync: conflict/version semantics and server acknowledgement of idempotency keys.

Cross-cutting requirements: TLS only, documented auth scopes, rate-limit headers,
stable error codes, pagination, server clock, data retention/deletion, upload limits,
WebSocket/SSE reconnect rules, and a published OpenAPI contract.

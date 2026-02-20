# V2 Architecture Explained

Reference diagram file: `docs/ARCHITECTURE_V2.mmd`

## How the system works
1. User interacts through the web app (chat, voice, file upload).
2. Frontend sends requests to backend API.
3. API enforces authentication, role checks, and tenant isolation.
4. LLM Orchestrator decides whether to answer directly or call tools.
5. Tools read/write business data (inventory, customers, orders) and trigger notifications.
6. Rules Engine runs automated jobs (low-stock alerts, daily owner reports).
7. Notification Gateway delivers WhatsApp/SMS/Email and records delivery outcomes.
8. Analytics service computes KPIs and feeds dashboard widgets.
9. Audit log store captures security and business events.
10. Monitoring tracks failures/latency, while backups protect database recovery.

## Main components and responsibilities
- `Frontend`: user interaction, voice capture, file upload, dashboard rendering.
- `API`: entry point, request validation, auth, tenant context propagation.
- `Auth + RBAC`: controls who can view/edit/send.
- `LLM Orchestrator`: prompt routing, tool-calling logic, provider abstraction.
- `Tool Layer`: domain actions (inventory checks, order lookup, message generation).
- `Rules Engine`: proactive automation (event-driven and scheduled).
- `Notification Gateway`: external delivery abstraction with retries and logs.
- `PostgreSQL`: source of truth for tenant and operational data.
- `Redis`: queueing, caching, schedule locks, task coordination.
- `Object Storage`: files uploaded by users and derived artifacts.
- `Audit Log Store`: immutable event trail for compliance and troubleshooting.
- `Analytics + Dashboard`: operational insight and outcome tracking.
- `Monitoring + Backup`: reliability and disaster recovery.

## Why this architecture is sellable
- Works for multiple industries via tenant templates.
- Clear separation between business logic and AI logic.
- Easy to add channels/providers without rewriting core app.
- Production controls included: auth, audit, monitoring, backup.

## Suggested deployment topology
- `Frontend`: static hosting (CDN or GitHub Pages for demo).
- `Backend API`: container service (Render/Fly/EC2/K8s).
- `PostgreSQL`: managed database (RDS/Neon/Supabase).
- `Redis`: managed cache/queue.
- `Object Storage`: S3-compatible bucket.
- `Monitoring`: hosted logs + metrics.

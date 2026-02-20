# AI Project Assistant V2 Implementation Roadmap

## Goal
Ship a production-ready, sellable multi-tenant business assistant with:
- LLM orchestration + tools
- business data platform (inventory/customers/orders)
- notifications
- automation rules
- multilingual voice quality controls
- security/compliance baseline
- analytics

## Scope Buckets (Requested Features)
1. Replace simulated response engine with real backend/API orchestration.
2. Add data layer for inventory/customers/orders with auth and roles.
3. Add owner/customer notifications (WhatsApp/SMS/Email).
4. Add workflow automation (low stock + scheduled reports).
5. Add multilingual speech QA and fallback logic.
6. Add tenant templates by industry.
7. Add audit logs, encryption, and backups.
8. Add analytics dashboard and operational KPIs.

## Phased Delivery Plan

### Phase 1: Foundation (Weeks 1-2)
**Objective:** make the app real backend-driven with secure identity basics.

- Build backend API (`FastAPI`) with clear modules:
  - `auth`, `chat`, `inventory`, `customers`, `orders`, `notifications`, `analytics`, `rules`.
- Introduce real LLM orchestration service:
  - provider abstraction (`OpenAI`, future providers)
  - tool-calling layer (inventory lookup, order status, pricing template, alert generation).
- Add PostgreSQL as primary DB (keep SQLite only for local dev/testing).
- Implement auth + roles:
  - `Owner`, `Manager`, `Staff`, optional `ReadOnly`.
- Wire frontend chat to backend `/api/chat` endpoint.

**Exit Criteria**
- No simulated `generateAIResponse()`.
- Login, role checks, tenant-aware API calls working.

### Phase 2: Core Business Platform (Weeks 3-4)
**Objective:** deliver actual business workflows.

- Data models:
  - `Tenant`, `User`, `InventoryItem`, `Customer`, `Order`, `OrderLine`, `PriceUpdate`.
- CRUD APIs and validation.
- Bulk upload/import support (CSV/Excel via backend parse pipeline).
- Business workflows:
  - remaining stock tracking
  - order lifecycle tracking
  - customer communication templates with context values.

**Exit Criteria**
- Business data visible and actionable in app.
- Assistant can query/update live records.

### Phase 3: Notifications + Automation (Weeks 5-6)
**Objective:** proactive operations, not only reactive chat.

- Notification gateway abstraction:
  - WhatsApp provider (Twilio/Meta)
  - SMS (Twilio)
  - Email (SMTP/SendGrid).
- Rules engine:
  - threshold rules (`stock <= reorder_level`)
  - time-based scheduler (daily owner summary at configured time)
  - event-based rules (new order, delayed order, unpaid invoice).
- Delivery logs + retry strategy + dead-letter queue.

**Exit Criteria**
- Owner gets low-stock + daily report automatically.
- Customer messages can be sent from approved templates.

### Phase 4: Speech QA + Templates + Analytics (Weeks 7-8)
**Objective:** improve quality and product fit per industry.

- Speech quality layer:
  - locale support registry
  - fallback language chain
  - confidence threshold handling (ask for confirmation if low).
- Tenant templates by industry:
  - Retail, Restaurant, Clinic/Pharmacy, Service Business, General.
- Analytics dashboard:
  - message outcomes
  - alert response times
  - stock-out prevention indicators
  - template usage and conversion metrics.

**Exit Criteria**
- Business onboarding template sets tenant defaults.
- KPI dashboard available for owner/admin roles.

### Phase 5: Security + Reliability Hardening (Weeks 9-10)
**Objective:** production sales readiness.

- Security:
  - encryption at rest and in transit
  - secret management
  - PII masking strategy for logs.
- Audit logs:
  - who changed what and when
  - chat/tool action logs by role/tenant.
- Backups:
  - daily DB backup + restore drills
  - retention policy and integrity checks.
- Observability:
  - centralized logging
  - metrics + alerts (uptime, queue lag, failures).

**Exit Criteria**
- Recovery tested.
- Audit and compliance baseline documented.

## Recommended Tech Choices
- API: `FastAPI`
- ORM/Migrations: `SQLAlchemy` + `Alembic`
- Database: `PostgreSQL` (prod), `SQLite` (dev)
- Queue/Scheduler: `Celery` + `Redis` (or `RQ`)
- Notifications: Twilio + SMTP/SendGrid
- Auth: JWT + refresh tokens, role-based access control
- Analytics: materialized views + API endpoints + frontend charts

## Risks and Controls
- Provider lock-in:
  - use adapter interfaces for LLM and notifications.
- Message delivery failure:
  - retries + status webhooks + dead-letter queue.
- Cross-tenant data leakage:
  - strict tenant scoping in every query + tests.
- Low speech accuracy in some locales:
  - confidence checks + manual confirm flow + language fallback.

## Suggested Backlog (First 12 Tickets)
1. Create backend service skeleton and module structure.
2. Implement tenant/user/auth models and RBAC middleware.
3. Build `/api/chat` with LLM orchestration and tool interfaces.
4. Implement inventory CRUD + low-stock fields.
5. Implement customers and orders CRUD.
6. Replace frontend simulated replies with API calls.
7. Add notification provider abstraction.
8. Implement low-stock event rule.
9. Implement daily owner summary scheduler.
10. Add audit logging middleware.
11. Add analytics endpoints for alert SLA and stock-out risk.
12. Create tenant template seeding per industry.

## Definition of Done (V2)
- Multi-tenant, role-secured, backend-driven assistant.
- Inventory/customers/orders operational.
- Automated owner/customer notifications live.
- KPI dashboard and audit trail available.
- Backup/restore and incident runbook validated.

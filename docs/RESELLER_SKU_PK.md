# WhatsApp Bot Reseller SKU (Pakistan)

Target: SMBs in Pakistan needing booking/sponsor automation and MFA support.

Plan tiers
- Starter PK: PKR 6,500/mo includes 5,000 conversations total (any category). Overage: PKR 1.0/conversation.
- Growth PK: PKR 16,500/mo includes 15,000 conversations. Overage: PKR 0.8/conversation.
- Scale PK: PKR 39,000/mo includes 40,000 conversations. Overage: PKR 0.7/conversation.

Included
- Hosting of the WhatsApp bot (1 number) on shared cluster.
- Webhook, signature validation, rate limiting, idempotency.
- Basic booking and sponsor intents; default replies.
- Health endpoint and monitoring.

Add-ons
- Dedicated container (per-tenant) PKR 8,000/mo.
- Custom templates setup (up to 5) PKR 4,000 one-time.
- Extra numbers: PKR 3,000/mo each (plus Meta fees).

Billing model
- Meta conversation/message fees are passed through at cost (see scripts/pricing_calculator.py).
- You bill the plan fee + any overage + any add-ons.

SLA
- Uptime target 99.5% monthly for shared hosting.
- Support response within 1 business day via WhatsApp/email.

Go-live checklist
- Number onboarded to WABA (phone_number_id + long-lived token + app secret).
- Webhook URL set to your deployed bot with verify token.
- At least one approved template for outbound (if needed).
- Environment variables configured and health check passing.

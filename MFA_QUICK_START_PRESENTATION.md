# MFA/2FA QUICK START – PRESENTATION PACK (Monday)

Status: Ready to present  
Audience: Sponsors, partners, clients  
Date: February 26, 2026

---

## What you will demo
- TOTP-based MFA (Microsoft/Google/Oracle Authenticator)
- Backup recovery codes (hashed at rest)
- Optional WhatsApp channel for remote MFA setup and booking/sponsor triage

---

## Pre-demo checklist (10 minutes)
1) Seed demo data + QR codes  
   `python MFA_DEMO_SETUP.py`
2) (Optional) Regenerate high-res QR PNGs  
   `python generate_qr_codes.py`
3) Verify TOTP end-to-end  
   `python MFA_VERIFY_SETUP.py`
4) Start WhatsApp bot (business inbox)  
   `make run-whatsapp-bot`
5) Expose webhook for Meta (while demoing)  
   `make tunnel` → set the https URL + your `WHATSAPP_VERIFY_TOKEN` in Meta

---

## Live demo flow (scripted, 5–7 minutes)
- Login with demo account: username `demo_user`, password `demo123`.
- Show Security panel: status “MFA enabled” and recovery codes visible.
- Scan pre-generated QR with Microsoft Authenticator; read out rotating 6-digit code.
- Enter code; highlight success banner and stored hashed recovery codes.
- Switch to WhatsApp Business number: send “book” and “sponsor” from another phone to show automated replies and the same MFA help channel if needed.

---

## Commands (copy/paste)
```bash
# Seed + QR codes
python MFA_DEMO_SETUP.py

# Verify TOTP works (DB + code)
python MFA_VERIFY_SETUP.py

# WhatsApp bot (requires env)
make run-whatsapp-bot      # Flask webhook on :5000
make tunnel                # ngrok tunnel for Meta webhook
```

Environment keys (set in `.env`):
```
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_VERIFY_TOKEN=
```

---

## Files you actually need today
- `MFA_DEMO_SETUP.py` — seed demo accounts, secrets, QR PNGs
- `generate_qr_codes.py` — regenerate QR codes (hi-res)
- `MFA_VERIFY_SETUP.py` — sanity check DB + TOTP
- `whatsapp_bot/app.py` — WhatsApp business webhook (book/sponsor/MFA helper)
- `scripts/run_whatsapp_bot.ps1` — one-command runner
- `Makefile` — `run-whatsapp-bot`, `tunnel`

Removed/deprecated: `MFA_DEMO_SETUP.py + MFA_VERIFY_SETUP.py (legacy desktop app removed)` (legacy desktop app)

---

## Security talking points
- TOTP (RFC 6238), 30s window, per-user secrets.
- Recovery codes hashed with SHA-256 at rest; never displayed after first show.
- No secrets in code; all env-driven; WhatsApp token/phone IDs via `.env`.
- Demo uses SQLite; ready to swap to Postgres/MySQL in production.
- WhatsApp channel uses Meta Cloud API with verify token challenge.

---

## Troubleshooting quick hits
- Codes failing: check system clock sync; re-scan QR; try recovery code.
- QR won’t scan: use “Enter setup key” from `MFA_DEMO_SETUP` output.
- WhatsApp not responding: confirm `WHATSAPP_*` envs, restart bot, ensure ngrok URL is set in Meta, and event subscription includes `messages`.
- DB check: `python check_db.py`

---

## Monday run-of-show (suggested)
- T‑5m: run steps 1–3; open ngrok tunnel; paste webhook URL.
- T‑2m: open QR PNG on screen; keep authenticator open.
- Demo: TOTP first, then WhatsApp “book”/“sponsor” flow.
- Close: recap security controls and handoff steps.

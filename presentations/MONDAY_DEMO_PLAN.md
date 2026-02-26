# Monday Demo Plan (MFA + WhatsApp Bot)

## Objectives
- Show working TOTP MFA with recovery codes.
- Demonstrate WhatsApp Business bot for booking/sponsor intake and MFA assistance.
- Keep setup friction low: everything runnable with two commands.

## Prep (10 minutes)
- `python MFA_DEMO_SETUP.py` (seed demo data, secrets, QR PNGs)
- `python MFA_VERIFY_SETUP.py` (sanity check)
- `make run-whatsapp-bot` (start webhook on :5000)
- `make tunnel` (ngrok https URL → paste into Meta webhook; set verify token)
- Open `qr_codes/` PNG for on-screen scan; keep authenticator app open.

## Demo Script (5–7 minutes)
- Log in as `demo_user` / `demo123`.
- Show Security panel with “MFA enabled” + recovery codes.
- Scan QR with Microsoft Authenticator; read out 6-digit TOTP; enter to confirm.
- Switch to WhatsApp: send “book” then “sponsor” from another phone to show replies.
- Mention security: TOTP (RFC 6238), hashed recovery codes, env-only secrets, verify token challenge on webhook.

## Required env
- `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_VERIFY_TOKEN`

## Files to keep handy
- `MFA_DEMO_SETUP.py`, `generate_qr_codes.py`, `MFA_VERIFY_SETUP.py`
- `whatsapp_bot/app.py`, `scripts/run_whatsapp_bot.ps1`, `Makefile`

## Contingencies
- If TOTP fails: re-scan QR, check system clock, use recovery code.
- If WhatsApp silent: restart bot, confirm env vars, ensure Meta webhook uses current ngrok URL and `messages` subscription.

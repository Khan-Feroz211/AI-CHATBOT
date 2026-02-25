# MFA Setup Guide (Authenticator App)

This guide explains how to enable and use 2FA (MFA) in **AI Project Assistant Pro**.

## What You Need

- A registered (non-guest) account in the app
- An authenticator app on your phone:
  - Google Authenticator
  - Microsoft Authenticator
  - Authy (or any TOTP-compatible app)

## Installed Dependencies

MFA requires:

- `pyotp`
- `qrcode[pil]`

They are already added to:

- `requirements.txt`
- `requirements-docker.txt`
- `requirements-simple.txt`

## Enable MFA

1. Launch the app:
```bash
python enhanced_chatbot_pro.py
```
2. Log in with your registered account.
3. Open MFA settings:
   - Header button: `🔐 Security`
   - Or menu: `Edit -> Security (2FA)`
4. Click `Generate QR Setup`.
5. Scan the QR code using your authenticator app.
6. Enter the current 6-digit code from your app.
7. Click `Enable MFA`.
8. Save your backup codes in a safe place.

## Login With MFA

1. Enter username and password as normal.
2. If MFA is enabled, app prompts for:
   - 6-digit authenticator code, or
   - backup recovery code
3. Enter code to complete login.

## Disable MFA

1. Go to `🔐 Security` settings.
2. Click `Disable MFA`.
3. Enter a valid authenticator code or backup code.

## Security Notes

- Backup codes are one-time use.
- Do not share authenticator seeds or backup codes.
- Keep `.env` and database files private.
- Rotate sensitive tokens/secrets periodically.

## Demo Checklist (Client Presentation)

1. Show normal login (username + password).
2. Show MFA challenge prompt.
3. Enter valid authenticator code and log in.
4. Show Security screen status = `Enabled`.
5. Show that login fails if MFA code is missing/invalid.

## Troubleshooting

- **"MFA libraries are not installed"**
  - Run:
```bash
pip install pyotp qrcode[pil]
```

- **QR not visible**
  - Ensure Pillow is installed (`qrcode[pil]` includes it).
  - Re-open Security dialog and regenerate QR.

- **Code rejected**
  - Check phone time is automatic/synced.
  - Try next code after 30 seconds.
  - Use a backup code if needed.

# MFA Quick Reference Guide

## Quick Start - 5 Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
# Includes: pyotp, qrcode[pil], cryptography, python-jose
```

### 2. Configure Environment
```bash
# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env:
TOTP_ENCRYPTION_KEY=<generated-key>
JWT_SECRET_KEY=<random-secret>
ADMIN_API_KEY=admin-secret-key
```

### 3. Initialize Database
```bash
python -c "from src.core.database import init_database; init_database()"
# Creates 5 MFA tables
```

### 4. Start Flask App
```bash
python -c "from src.main import create_app; app = create_app(); app.run(debug=True)"
# MFA endpoints now available at /api/auth/*
```

### 5. Test Setup
```bash
curl -X POST http://localhost:5000/api/auth/mfa/setup \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "phone_number": "+923001234567",
    "authenticator_type": "microsoft"
  }'
```

## Common Tasks

### Verify a User's Code

```python
from src.auth.mfa import MFAService

mfa = MFAService(encryption_key='your-key')

if mfa.verify_mfa_code(client_id=123, code='123456'):
    # User authenticated - create session
    pass
```

### Create Session After Auth

```python
from src.auth.session import SessionManager

session_mgr = SessionManager()

session = session_mgr.create_session(
    client_id=123,
    phone_number='+923001234567',
    mfa_verified=True
)

# Return tokens to client
access_token = session['access_token']
refresh_token = session['refresh_token']
```

### Protect API Endpoint

```python
from flask import request, jsonify
from src.auth.session import SessionTokenManager

token_mgr = SessionTokenManager()

@app.route('/api/protected')
def protected_resource():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    claims = token_mgr.verify_token(token)
    
    if not claims or not claims.get('mfa_verified'):
        return {'error': 'Authentication required'}, 401
    
    return {'data': 'secret'}, 200
```

### Check Rate Limiting

```python
from src.auth.mfa import MFARateLimiter

limiter = MFARateLimiter()

is_locked, minutes = limiter.check_lockout('+923001234567')

if is_locked:
    print(f"Account locked for {minutes} more minutes")
else:
    # Proceed with auth attempt
    pass
```

### Generate QR Code

```python
from src.auth.qr_generator import QRCodeGenerator
from src.auth.mfa import TOTPManager

totp = TOTPManager()
secret = totp.generate_secret()

# Generate QR
qr = QRCodeGenerator.generate_microsoft_authenticator_qr(secret, '+923001234567')

# Get as bytes for WhatsApp
qr_bytes = QRCodeGenerator.image_to_bytes(qr)

# Or save to file
path = QRCodeGenerator.save_qr_to_file(qr, 'client_123')
```

### Get Instructions for User

```python
from src.auth.qr_generator import QRCodeGenerator

instructions = QRCodeGenerator.generate_setup_instructions('microsoft')
# Returns formatted WhatsApp message with step-by-step setup

whatsapp_client.send_message(phone_number, instructions)
```

### List User's Active Sessions

```python
from src.auth.session import SessionManager

session_mgr = SessionManager()

sessions = session_mgr.get_active_sessions(client_id=123)
# Returns list of active sessions with device info, IP, etc.
```

### Logout User

```python
from src.auth.session import SessionManager

session_mgr = SessionManager()

# Logout from current device
session_mgr.invalidate_session(client_id=123, token=access_token)

# Or logout from all devices
session_mgr.invalidate_session(client_id=123)
```

### View Authentication Logs

```bash
# Via API (requires admin key)
curl -X GET 'http://localhost:5000/api/auth/admin/mfa/logs?client_id=123&limit=10' \
  -H "X-Admin-Key: <admin-key>"

# Or in Python
from src.core.database import get_session_context
from src.auth.mfa_models import MFAAttempt

with get_session_context() as session:
    logs = session.query(MFAAttempt)\
        .filter_by(client_id=123)\
        .order_by(MFAAttempt.created_at.desc())\
        .limit(10)\
        .all()
    
    for log in logs:
        print(f"{log.created_at}: {log.attempt_type} - Success: {log.success}")
```

## API Endpoints

### User Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/mfa/setup` | Start MFA setup |
| POST | `/api/auth/mfa/verify` | Verify TOTP code |
| POST | `/api/auth/mfa/backup-code` | Use backup code |
| POST | `/api/auth/token/refresh` | Refresh access token |

### Admin Endpoints (Require X-Admin-Key header)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/admin/mfa/reset` | Reset MFA for user |
| GET | `/api/auth/admin/mfa/logs` | View auth logs |
| POST | `/api/auth/admin/mfa/whitelist` | Whitelist phone |
| DELETE | `/api/auth/admin/mfa/whitelist/<phone>` | Remove whitelist |

## Database Models

```python
from src.auth.mfa_models import (
    MFASetup,          # User MFA configuration
    MFASession,        # Active sessions
    MFAAttempt,        # Auth logs
    MFALockout,        # Rate limiting
    MFABackupCode      # Emergency codes
)
```

## Configuration Reference

### TOTP (Time-based One-Time Password)
- **Standard**: RFC 6238
- **Code Length**: 6 digits
- **Time Step**: 30 seconds
- **Time Window**: ±1 step (60 seconds total)
- **Supported Apps**: Microsoft Authenticator, Oracle Mobile Authenticator, Google Authenticator, Authy

### Rate Limiting
- **Threshold**: 5 failed attempts
- **Lockout Duration**: 15 minutes
- **Counter Reset**: On successful auth

### Backup Codes
- **Count**: 8 codes per user
- **Format**: 8 characters (alphanumeric)
- **Usage**: Single-use emergency access
- **Storage**: SHA-256 hashed

### Sessions
- **Token Type**: JWT (JSON Web Token)
- **Access Token Expiry**: 24 hours
- **Refresh Token Expiry**: 7 days
- **Algorithm**: HS256 (HMAC-SHA256)

### Encryption
- **Method**: Fernet (symmetric)
- **Library**: cryptography
- **Key**: 32 bytes (base64-encoded)
- **Applies To**: TOTP secrets, backup codes

## Troubleshooting

### TOTP Code Always Invalid
```
Possible Causes:
1. Phone clock is significantly off
2. Code typed within wrong time window
3. Current code already used (wait 30 seconds)
4. Incorrect secret in database
```

### Session Token Expired
```
Solution:
1. Use refresh_token to get new access_token
2. If refresh_token also expired, user must re-authenticate
```

### Can't Scan QR Code
```
Possible Fixes:
1. Ensure QR has high contrast
2. Check authenticator app supports otpauth:// protocol
3. Try manual entry: otpauth://totp/...
4. Ensure good lighting for camera
```

### Rate Limit Lockout
```
Resolution:
1. Admin API: POST /api/auth/admin/mfa/reset
2. Or wait 15 minutes
3. Check logs: GET /api/auth/admin/mfa/logs
```

### Backup Codes Not Working
```
Debug Steps:
1. Verify code format (8 chars)
2. Check code not already used
3. Verify client_id correct
4. Review MFA logs for errors
```

## Performance Considerations

| Operation | Time | Notes |
|-----------|------|-------|
| TOTP verification | <5ms | Includes decryption |
| QR generation | ~100ms | Depends on image size |
| Session creation | ~50ms | Database write |
| Rate limit check | <5ms | In-memory after DB load |
| Backup code hash | <10ms | SHA-256 computation |

## Security Checklist

- [ ] `TOTP_ENCRYPTION_KEY` is strong and random
- [ ] `JWT_SECRET_KEY` is long (32+ chars)
- [ ] `ADMIN_API_KEY` is not default/weak
- [ ] Database backups include encrypted secrets
- [ ] HTTPS enabled for all auth endpoints
- [ ] Audit logs monitored for suspicious patterns
- [ ] Failed login alerts configured
- [ ] Session timeout configured appropriately
- [ ] Backup codes securely delivered to users
- [ ] Rate limiting tested with load testing

## Integration Checklist

- [ ] MFA models created in database
- [ ] Environment variables configured
- [ ] Flask blueprint registered in app
- [ ] WhatsApp webhook updated with MFA intent handling
- [ ] QR code delivery mechanism implemented
- [ ] Session validation added to protected endpoints
- [ ] Admin API secured with key authentication
- [ ] Audit logging configured
- [ ] Error messages user-friendly
- [ ] Mobile-friendly setup flow tested

## Future Enhancements

1. **Email delivery** of backup codes and setup links
2. **SMS delivery** of one-time codes alternative to authenticator
3. **WebAuthn** support (fingerprint/face recognition)
4. **Device trust** - remember device for 30 days
5. **MFA enforcement** - require MFA for admin users
6. **Passwordless** - replace password + MFA with authenticator only
7. **Recovery email** - secondary account recovery method
8. **Push notifications** - approve login via app notification

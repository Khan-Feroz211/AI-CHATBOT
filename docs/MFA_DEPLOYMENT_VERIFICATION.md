# MFA Deployment Verification Checklist

## Pre-Deployment Verification

### 1. Dependencies Installed
```bash
# Verify all required packages installed
pip freeze | grep -E "pyotp|qrcode|Pillow|python-jose|cryptography"

# Expected output (or similar versions):
# cryptography==41.0.7
# Pillow==10.0.0
# pyotp==2.9.0
# python-jose==3.3.0
# qrcode==7.4.2
```

**Status:** ☐ VERIFIED

### 2. Environment Variables
```bash
# Check .env file has required variables
cat .env | grep -E "TOTP_ENCRYPTION_KEY|JWT_SECRET_KEY|ADMIN_API_KEY"

# Generate missing keys if needed:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Required Variables:**
- [ ] TOTP_ENCRYPTION_KEY (Fernet key)
- [ ] JWT_SECRET_KEY (random 32+ chars)
- [ ] ADMIN_API_KEY (unique admin key)
- [ ] DATABASE_URL (if different from default)
- [ ] COMPANY_NAME (optional, defaults to "WhatsApp Inventory Bot")

**Status:** ☐ VERIFIED

### 3. Database Setup
```bash
# Start Python shell in project directory
python

# In Python:
from src.core.database import init_database
from src.core.config import get_config

config = get_config()
init_database(config)

# Verify tables created:
from src.core.database import get_session_context
from sqlalchemy import inspect

with get_session_context() as session:
    inspector = inspect(session.bind)
    tables = inspector.get_table_names()
    required_tables = ['mfa_setup', 'mfa_attempt', 'mfa_session', 'mfa_lockout', 'mfa_backup_codes']
    
    for table in required_tables:
        if table in tables:
            print(f"✓ {table}")
        else:
            print(f"✗ {table} - MISSING!")
```

**Expected Tables:**
- [ ] mfa_setup
- [ ] mfa_attempt
- [ ] mfa_session
- [ ] mfa_lockout
- [ ] mfa_backup_codes

**Status:** ☐ VERIFIED

### 4. Code Structure
```bash
# Verify all auth module files exist
ls -la src/auth/

# Expected files:
# __init__.py
# mfa.py
# mfa_models.py
# qr_generator.py
# session.py
# routes.py
```

**Expected Files:**
- [ ] src/auth/__init__.py
- [ ] src/auth/mfa.py
- [ ] src/auth/mfa_models.py
- [ ] src/auth/qr_generator.py
- [ ] src/auth/session.py
- [ ] src/auth/routes.py

**Status:** ☐ VERIFIED

### 5. Flask App Integration
```python
# Test that Flask app initializes with MFA
from src.main import create_app

app = create_app()

# Verify auth blueprint registered
print(app.blueprints)
# Should include 'auth' blueprint with routes like:
# /api/auth/mfa/setup
# /api/auth/mfa/verify
# /api/auth/mfa/backup-code
# /api/auth/token/refresh
# /api/auth/admin/mfa/reset (admin)
# /api/auth/admin/mfa/logs (admin)
# /api/auth/admin/mfa/whitelist (admin)
```

**Status:** ☐ VERIFIED

### 6. Import Verification
```python
# Verify all modules import correctly
from src.auth.mfa import (
    MFAService,
    TOTPManager,
    BackupCodeManager,
    MFARateLimiter,
    TOTPEncryption
)

from src.auth.session import (
    SessionManager,
    SessionTokenManager,
    DeviceFingerprint,
    SessionConfig
)

from src.auth.qr_generator import (
    QRCodeGenerator,
    WhatsAppQRSender
)

from src.auth.mfa_models import (
    MFASetup,
    MFASession,
    MFAAttempt,
    MFALockout,
    MFABackupCode
)

print("✓ All imports successful")
```

**Status:** ☐ VERIFIED

### 7. Route Registration
```python
from src.main import create_app

app = create_app()

# Check registered routes
for rule in app.url_map.iter_rules():
    if 'auth' in rule.rule:
        print(f"{rule.methods} {rule.rule}")

# Expected output (sorted by path):
# GET, OPTIONS /api/auth/health
# POST /api/auth/mfa/backup-code
# POST /api/auth/mfa/setup
# POST /api/auth/mfa/verify
# POST /api/auth/token/refresh
# DELETE /api/auth/admin/mfa/whitelist/<phone_number>
# GET /api/auth/admin/mfa/logs
# POST /api/auth/admin/mfa/reset
# POST /api/auth/admin/mfa/whitelist
```

**Status:** ☐ VERIFIED

## API Testing

### 1. Health Check
```bash
curl -X GET http://localhost:5000/api/auth/health

# Expected response:
# {"status":"healthy"}
```

**Status:** ☐ VERIFIED

### 2. MFA Setup
```bash
curl -X POST http://localhost:5000/api/auth/mfa/setup \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "phone_number": "+923001234567",
    "authenticator_type": "microsoft"
  }'

# Expected response:
# {
#   "status": "setup_initiated",
#   "message": "QR code and instructions sent",
#   "backup_codes": ["CODE1", "CODE2", ...],
#   "authenticator_type": "microsoft",
#   "expires_in_minutes": 30
# }
```

**Status:** ☐ VERIFIED

### 3. TOTP Verification
```bash
# Get current code (in Python):
from src.auth.mfa import TOTPManager

totp = TOTPManager()
secret = "YOUR_SECRET_FROM_QR"  # From setup response

code = totp.get_current_code(secret)
print(f"Current code: {code}")
time_remaining = totp.get_provisioning_time_remaining()
print(f"Code expires in: {time_remaining} seconds")

# Test with valid code:
curl -X POST http://localhost:5000/api/auth/mfa/verify \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "phone_number": "+923001234567",
    "code": "'"$code"'"
  }'

# Expected response:
# {
#   "status": "verified",
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "Bearer",
#   "expires_in": 86400
# }
```

**Status:** ☐ VERIFIED

### 4. Protected Endpoint Test
```bash
# Save tokens from previous response
ACCESS_TOKEN="<token-from-verify-response>"

# Try to access with valid token
curl -X ANY http://localhost:5000/api/protected \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Should be allowed (if endpoint uses @require_mfa decorator)
```

**Status:** ☐ VERIFIED

### 5. Rate Limiting Test
```bash
# Test rate limiting (5 failed attempts → lockout)
for i in {1..5}; do
  curl -X POST http://localhost:5000/api/auth/mfa/verify \
    -H "Content-Type: application/json" \
    -d '{
      "client_id": 1,
      "phone_number": "+923001234567",
      "code": "000000"
    }'
  sleep 1
done

# 6th attempt should be locked:
curl -X POST http://localhost:5000/api/auth/mfa/verify \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "phone_number": "+923001234567",
    "code": "000000"
  }'

# Expected response (status 429):
# {
#   "error": "Account locked",
#   "message": "Too many failed attempts. Try again in 15 minutes"
# }
```

**Status:** ☐ VERIFIED

### 6. Backup Code Test
```bash
# Get backup codes from setup response
BACKUP_CODE="CODE1"  # First backup code from setup

curl -X POST http://localhost:5000/api/auth/mfa/backup-code \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "backup_code": "'"$BACKUP_CODE"'"
  }'

# Expected response:
# {
#   "status": "verified",
#   "access_token": "eyJ...",
#   "message": "Access granted. Please update your authenticator setup."
# }

# Second attempt with same code should fail (single-use):
curl -X POST http://localhost:5000/api/auth/mfa/backup-code \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "backup_code": "'"$BACKUP_CODE"'"
  }'

# Expected response (status 401):
# {"error": "Invalid backup code"}
```

**Status:** ☐ VERIFIED

### 7. Admin APIs Test
```bash
# Get logs (requires admin key)
curl -X GET 'http://localhost:5000/api/auth/admin/mfa/logs?client_id=1&limit=10' \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"

# Expected response:
# {
#   "logs": [...],
#   "total": n
# }

# Reset MFA
curl -X POST http://localhost:5000/api/auth/admin/mfa/reset \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY" \
  -d '{
    "client_id": 1,
    "reason": "Test reset"
  }'

# Expected response:
# {
#   "status": "reset",
#   "message": "MFA reset for client 1"
# }
```

**Status:** ☐ VERIFIED

## Database Verification

### 1. Table Structure
```python
from src.core.database import get_session_context
from src.auth.mfa_models import (
    MFASetup, MFASession, MFAAttempt, MFALockout, MFABackupCode
)
from sqlalchemy import inspect

with get_session_context() as session:
    for model in [MFASetup, MFASession, MFAAttempt, MFALockout, MFABackupCode]:
        mapper = inspect(model)
        print(f"\n{model.__name__}:")
        for col in mapper.columns:
            print(f"  {col.name}: {col.type}")
```

**Status:** ☐ VERIFIED

### 2. Data Integrity
```python
# Verify relationships work
from src.core.database import get_session_context
from src.auth.mfa_models import MFASetup
from src.core.models import Client

with get_session_context() as session:
    # Create test client (if not exists)
    client = Client(phone_number="+923001234567", name="Test User")
    session.add(client)
    session.commit()
    
    # Create MFA setup linked to client
    mfa_setup = MFASetup(client_id=client.id)
    session.add(mfa_setup)
    session.commit()
    
    # Verify relationship
    assert mfa_setup.client.phone_number == "+923001234567"
    print("✓ Relationships working correctly")
```

**Status:** ☐ VERIFIED

## Security Verification

### 1. Encryption Working
```python
from src.auth.mfa import TOTPEncryption
import os

encryption_key = os.getenv('TOTP_ENCRYPTION_KEY')
encryptor = TOTPEncryption(encryption_key)

# Test encryption/decryption
original_secret = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
encrypted = encryptor.encrypt_secret(original_secret)
decrypted = encryptor.decrypt_secret(encrypted)

assert original_secret == decrypted
print("✓ Encryption working correctly")
```

**Status:** ☐ VERIFIED

### 2. Rate Limiting Working
```python
from src.auth.mfa import MFARateLimiter

limiter = MFARateLimiter()

# Simulate 5 failed attempts
phone = "+923001234567"
for i in range(5):
    is_locked, minutes = limiter.check_lockout(phone)
    assert not is_locked, f"Locked before 5 attempts (attempt {i})"
    
    limiter.record_failed_attempt(phone, 1, "test")

# 6th attempt should be locked
is_locked, minutes = limiter.check_lockout(phone)
assert is_locked, "Not locked after 5 attempts"
assert minutes > 0, "Minutes remaining should be > 0"
print(f"✓ Rate limiting working (locked for {minutes} minutes)")
```

**Status:** ☐ VERIFIED

### 3. Session Token Working
```python
from src.auth.session import SessionTokenManager
import os

token_mgr = SessionTokenManager()

# Create token
token = token_mgr.create_access_token(
    client_id=123,
    phone_number="+923001234567",
    mfa_verified=True
)

# Verify token
claims = token_mgr.verify_token(token)
assert claims is not None
assert claims['sub'] == '123'
assert claims['mfa_verified'] == True
print("✓ Session tokens working correctly")
```

**Status:** ☐ VERIFIED

## Documentation Verification

### 1. Check Documentation Files
```bash
# Verify documentation exists and is readable
ls -l docs/MFA_*.md

# Expected files:
# docs/MFA_IMPLEMENTATION.md (500+ lines)
# docs/MFA_QUICK_REFERENCE.md (300+ lines)
```

**Status:** ☐ VERIFIED

### 2. Check Example Code
```bash
# Verify example code in documentation is correct
grep -n "from src.auth" docs/MFA_*.md | head -10

# Should show import examples that match actual module structure
```

**Status:** ☐ VERIFIED

## Performance Verification

### 1. Response Time Test
```python
import time
from src.auth.mfa import TOTPManager, MFARateLimiter
from src.auth.session import SessionTokenManager

# TOTP verification (target: <5ms)
totp = TOTPManager()
secret = totp.generate_secret()

start = time.time()
for _ in range(100):
    totp.verify_code(secret, "000000")
elapsed = (time.time() - start) / 100
print(f"TOTP verification: {elapsed*1000:.2f}ms per call")

# Token verification (target: <5ms)
token_mgr = SessionTokenManager()
token = token_mgr.create_access_token(123, "+923001234567")

start = time.time()
for _ in range(100):
    token_mgr.verify_token(token)
elapsed = (time.time() - start) / 100
print(f"Token verification: {elapsed*1000:.2f}ms per call")
```

**Expected Performance:**
- [ ] TOTP verification: <5ms
- [ ] Token verification: <5ms
- [ ] Session creation: <50ms
- [ ] Rate limit check: <5ms

**Status:** ☐ VERIFIED

## Final Checklist

### Development Ready
- [ ] All 5 MFA database tables created
- [ ] All imports working
- [ ] All routes registered
- [ ] Environment variables configured
- [ ] API health check passing
- [ ] At least one MFA setup → verify flow successful
- [ ] Rate limiting tested
- [ ] Backup codes tested
- [ ] Admin endpoints working

### Production Ready (Additional)
- [ ] HTTPS enabled
- [ ] Secrets stored securely (not in git)
- [ ] Database backups automated
- [ ] Logging to persistent storage
- [ ] Monitoring/alerts configured
- [ ] Load testing completed
- [ ] Error messages user-friendly
- [ ] Audit logs being generated
- [ ] Session cleanup job scheduled
- [ ] Rate limit thresholds reviewed

### Deployment Steps
1. [ ] Pull latest code
2. [ ] Install/update dependencies: `pip install -r requirements.txt`
3. [ ] Set environment variables in production
4. [ ] Run database initialization: `python -c "from src.core.database import init_database; init_database()"`
5. [ ] Run test suite: `pytest tests/auth/`
6. [ ] Start application: `python app.py` or `gunicorn wsgi:app`
7. [ ] Verify health endpoint: `curl http://localhost:5000/api/auth/health`
8. [ ] Test with real client: Full MFA flow

## Rollback Plan

If issues encountered:

1. **Database Issues**
   ```bash
   # Backup current database
   cp data/inventory_bot.db data/inventory_bot.db.backup
   
   # Drop MFA tables (development only):
   # DELETE FROM mfa_sessions;
   # DELETE FROM mfa_attempts;
   # DELETE FROM mfa_setup;
   # DELETE FROM mfa_lockout;
   # DELETE FROM mfa_backup_codes;
   ```

2. **Code Issues**
   ```bash
   # Revert to previous version
   git revert HEAD
   git pull
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

3. **Secrets Issues**
   ```bash
   # Regenerate encryption keys
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   
   # Update .env with new keys
   vim .env
   ```

## Support Contacts

For issues:
1. Check `MFA_QUICK_REFERENCE.md` troubleshooting section
2. Review logs in latest Flask output
3. Check `docs/MFA_IMPLEMENTATION.md` for detailed architecture
4. Run diagnostic: `python scripts/tools/diagnose_auth_issues.py`

---

**Deployment Status:** ☐ NOT STARTED ☐ IN PROGRESS ☐ COMPLETE

**Date Verified:** _________________

**Verified By:** _________________

**Notes:** _________________________________________________________

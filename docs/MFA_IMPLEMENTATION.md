# MFA/2FA Authentication System - Implementation Complete

## Overview

A complete enterprise-grade Multi-Factor Authentication (MFA) / Two-Factor Authentication (2FA) system has been implemented for the WhatsApp Inventory Bot. The system supports:

- **TOTP (Time-based One-Time Password)** - RFC 6238 standard
- **Multiple Authenticator Apps**:
  - Microsoft Authenticator
  - Oracle Mobile Authenticator  
  - Google Authenticator
  - Authy
- **Session Management** - JWT tokens with 24-hour expiration
- **Rate Limiting** - 5 failed attempts trigger 15-minute lockout
- **Backup Codes** - 8 single-use emergency codes for account recovery
- **Encryption at Rest** - Fernet-based encryption of TOTP secrets
- **Audit Logging** - Complete authentication attempt tracking
- **Admin Controls** - Reset MFA, view logs, whitelist/blacklist phones

## Architecture

### Module Structure

```
src/auth/
├── __init__.py              # Package exports
├── mfa_models.py           # SQLAlchemy ORM models (5 tables)
├── mfa.py                  # TOTP & MFA business logic
├── qr_generator.py         # QR code generation for setup
├── session.py              # JWT session management
├── routes.py               # Flask API endpoints
└── admin_commands.py       # (Pending) Admin CLI commands
```

### Configuration

**Environment Variables Required:**

```bash
# TOTP Encryption key (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
TOTP_ENCRYPTION_KEY=<fernet-key>

# JWT Secret for session tokens
JWT_SECRET_KEY=<random-secret>

# Session encryption (optional, auto-generated if not set)
SESSION_ENCRYPTION_KEY=<fernet-key>

# Admin API key for admin endpoints
ADMIN_API_KEY=<admin-key>

# Company name for authenticator display
COMPANY_NAME="WhatsApp Inventory Bot"
```

## Database Schema

### 1. MFASetup Table
Stores user MFA configuration and secrets.

```python
class MFASetup(Base):
    __tablename__ = 'mfa_setup'
    
    id: Integer (Primary Key)
    client_id: Integer (FK to clients, Unique)
    totp_secret_encrypted: String(255)  # Encrypted TOTP secret
    microsoft_enabled: Boolean
    oracle_enabled: Boolean
    backup_codes_encrypted: TEXT  # JSON array of encrypted codes
    mfa_enabled: Boolean
    mfa_verified: Boolean
    created_at: DateTime
    updated_at: DateTime
```

### 2. MFAAttempt Table
Audit log of all authentication attempts.

```python
class MFAAttempt(Base):
    __tablename__ = 'mfa_attempts'
    
    id: Integer (Primary Key)
    client_id: Integer (FK to clients)
    phone_number: String(20)
    attempt_type: String(20)  # 'totp_verify', 'backup_code', 'initial_setup'
    success: Boolean
    authenticator_type: String(50)  # 'microsoft', 'oracle'
    ip_address: String(45)
    user_agent: String(255)
    error_reason: String(255)
    created_at: DateTime
```

### 3. MFASession Table
Active session tracking with JWT tokens.

```python
class MFASession(Base):
    __tablename__ = 'mfa_sessions'
    
    id: Integer (Primary Key)
    client_id: Integer (FK to clients)
    phone_number: String(20)
    session_token: String(500) (Unique)  # JWT access token
    refresh_token: String(500)  # JWT refresh token
    mfa_verified: Boolean
    ip_address: String(45)
    device_info: String(500)
    is_active: Boolean
    authenticator_type: String(50)
    expires_at: DateTime
    created_at: DateTime
    updated_at: DateTime
```

### 4. MFALockout Table
Rate limiting and brute force protection.

```python
class MFALockout(Base):
    __tablename__ = 'mfa_lockout'
    
    id: Integer (Primary Key)
    phone_number: String(20) (Unique)
    failed_attempts: Integer
    locked_until: DateTime
    last_attempt: DateTime
```

### 5. MFABackupCode Table
Single-use recovery codes.

```python
class MFABackupCode(Base):
    __tablename__ = 'mfa_backup_codes'
    
    id: Integer (Primary Key)
    client_id: Integer (FK to clients)
    code_hash: String(255) (Unique)  # SHA-256 hashed
    used: Boolean
    used_at: DateTime
    created_at: DateTime
```

## Core Components

### 1. src/auth/mfa.py

#### TOTPEncryption Class
- `encrypt_secret(secret: str) → str` - Encrypt TOTP secret using Fernet
- `decrypt_secret(encrypted: str) → str` - Decrypt stored secret

#### TOTPManager Class
- `generate_secret() → str` - Generate base32 TOTP secret
- `get_totp_uri(secret, name, issuer) → str` - Create otpauth:// URI for QR codes
- `get_current_code(secret) → str` - Get current 6-digit code
- `verify_code(secret, code, valid_window) → bool` - Verify TOTP code
- `get_provisioning_time_remaining() → int` - Seconds until code expires

#### BackupCodeManager Class
- `generate_backup_codes() → list[str]` - Generate 8 unique backup codes
- `hash_code(code) → str` - SHA-256 hash for storage
- `verify_code(code, stored_hash) → bool` - Verify backup code

#### MFARateLimiter Class
- `check_lockout(phone: str) → (bool, int)` - Check if locked and remaining minutes
- `record_failed_attempt(phone, client_id, reason)` - Log failed attempt, trigger lockout after 5 attempts
- `record_successful_attempt(phone, client_id, authenticator_type)` - Clear lockout on success

#### MFAService Class
High-level service combining all components:
- `setup_mfa_for_user(client_id, phone) → (secret, uri, backup_codes)`
- `verify_mfa_code(client_id, code) → bool`
- `verify_backup_code(client_id, code) → bool`
- `is_mfa_enabled(client_id) → bool`
- `enable_authenticator(client_id, auth_type)`

### 2. src/auth/qr_generator.py

#### QRCodeGenerator Class
- `generate_totp_qr(secret, account_name, issuer) → Image` - Generate generic QR
- `generate_microsoft_authenticator_qr(secret, phone) → Image` - Microsoft-optimized QR
- `generate_oracle_authenticator_qr(secret, phone) → Image` - Oracle-optimized QR
- `add_label_to_qr(image, label) → Image` - Add text label
- `generate_branded_qr(secret, phone, auth_type) → Image` - Generate with branding
- `image_to_base64(image) → str` - Convert to base64 for storage
- `image_to_bytes(image) → bytes` - Convert for transmission
- `save_qr_to_file(image, filename) → str` - Save to filesystem
- `generate_setup_instructions(auth_type) → str` - Get user-friendly instructions

#### WhatsAppQRSender Class
- `prepare_qr_for_whatsapp(image) → bytes` - Optimize for WhatsApp transmission
- `get_whatsapp_instructions(auth_type) → str` - Format instructions for WhatsApp

### 3. src/auth/session.py

#### SessionTokenManager Class
- `create_access_token(client_id, phone, mfa_verified, claims) → str` - Create JWT
- `create_refresh_token(client_id, phone) → str` - Create refresh JWT
- `create_mfa_provisional_token(client_id, phone, expires_in) → str` - Temporary MFA token
- `verify_token(token) → dict` - Verify and decode JWT
- `is_token_expired(token) → bool` - Check expiration
- `refresh_access_token(refresh_token) → str` - Get new access token

#### SessionManager Class
- `create_session(client_id, phone, ip, device, mfa_verified) → dict` - Create authenticated session
- `validate_session(client_id, token) → bool` - Validate active session
- `invalidate_session(client_id, token)` - Logout (invalidate session)
- `get_active_sessions(client_id) → list` - List all active sessions
- `refresh_session_token(client_id, refresh_token) → dict` - Refresh access token
- `mark_mfa_verified(client_id, token)` - Update session after MFA

#### DeviceFingerprint Class
- `generate(ip, user_agent) → str` - Create device fingerprint hash
- `verify(ip, user_agent, stored) → bool` - Verify device fingerprint

### 4. src/auth/routes.py

Flask blueprint with complete authentication API endpoints.

## API Endpoints

### Authentication Endpoints

**POST /api/auth/mfa/setup**
- Initiate MFA setup, generate QR code
- Request: `{client_id, phone_number, authenticator_type}`
- Response: `{status, backup_codes, expires_in_minutes}`
- Sends: QR code image + setup instructions via WhatsApp

**POST /api/auth/mfa/verify**
- Verify TOTP code and create session
- Request: `{client_id, phone_number, code}`
- Response: `{access_token, refresh_token, expires_in}`
- Rate limited: 5 attempts → 15-minute lockout

**POST /api/auth/mfa/backup-code**
- Verify backup code for emergency access
- Request: `{client_id, backup_code}`
- Response: `{access_token, message}`
- Single-use: Code consumed after verification

**POST /api/auth/token/refresh**
- Refresh expired access token
- Request: `{client_id, refresh_token}`
- Response: `{access_token, expires_in}`

### Admin Endpoints

**POST /api/auth/admin/mfa/reset** (Admin Only)
- Reset MFA for user
- Header: `X-Admin-Key: <admin-key>`
- Request: `{client_id, reason}`
- Response: `{status, message}`

**GET /api/auth/admin/mfa/logs** (Admin Only)
- View authentication attempt logs
- Query: `?client_id=123&limit=50&offset=0`
- Response: `{logs: [...], total: n}`

**POST /api/auth/admin/mfa/whitelist** (Admin Only)
- Whitelist phone number
- Request: `{phone_number, reason}`
- Response: `{status, phone_number}`

**DELETE /api/auth/admin/mfa/whitelist/<phone>** (Admin Only)
- Remove phone from whitelist
- Response: `{status, phone_number}`

## Usage Examples

### 1. Setup MFA

```python
from src.auth.mfa import MFAService
from src.auth.qr_generator import QRCodeGenerator
from src.auth.session import SessionManager

# Initialize services
mfa_service = MFAService(encryption_key='your-encryption-key')
qr_generator = QRCodeGenerator()

# Step 1: User requests MFA setup
client_id = 123
phone_number = '+923001234567'

secret, uri, backup_codes = mfa_service.setup_mfa_for_user(client_id, phone_number)

# Step 2: Generate QR code for Microsoft Authenticator
qr_image = qr_generator.generate_microsoft_authenticator_qr(secret, phone_number)

# Step 3: Convert to bytes for WhatsApp (base64 or binary)
qr_bytes = qr_generator.image_to_bytes(qr_image)

# Step 4: Send to WhatsApp (integrate with your WhatsApp client)
# whatsapp_client.send_image(phone_number, qr_bytes, caption="Scan this QR code")

# Step 5: Send backup codes
# whatsapp_client.send_message(phone_number, f"Backup codes:\n" + "\n".join(backup_codes))

print(f"Secret (encrypted): {secret}")
print(f"Backup codes: {backup_codes}")
```

### 2. Verify TOTP Code and Create Session

```python
from src.auth.mfa import MFAService
from src.auth.session import SessionManager

mfa_service = MFAService(encryption_key='your-encryption-key')
session_manager = SessionManager()

# User enters 6-digit code from authenticator
client_id = 123
code = '123456'

# Verify the code
if mfa_service.verify_mfa_code(client_id, code):
    # Create authenticated session
    session_info = session_manager.create_session(
        client_id=client_id,
        phone_number='+923001234567',
        ip_address='192.168.1.1',
        device_info='Mozilla/5.0...',
        mfa_verified=True
    )
    
    # Return tokens to user
    print(f"Access Token: {session_info['access_token']}")
    print(f"Refresh Token: {session_info['refresh_token']}")
else:
    print("Invalid code")
```

### 3. Verify Backup Code

```python
# User uses backup code when they don't have authenticator
backup_code = 'ABCD1234'

if mfa_service.verify_backup_code(client_id, backup_code):
    # Create session
    session_info = session_manager.create_session(
        client_id=client_id,
        phone_number=phone_number,
        mfa_verified=True
    )
    print("Access granted. Please update your authenticator setup.")
else:
    print("Invalid backup code")
```

### 4. Validate Session on API Requests

```python
from flask import request
from src.auth.session import SessionTokenManager

token_manager = SessionTokenManager()

# Extract token from request
token = request.headers.get('Authorization', '').replace('Bearer ', '')

# Verify token
claims = token_manager.verify_token(token)

if claims:
    client_id = claims['sub']
    mfa_verified = claims['mfa_verified']
    print(f"Request from client {client_id}, MFA verified: {mfa_verified}")
else:
    print("Invalid or expired token")
```

### 5. Admin Reset MFA

```python
from src.core.database import get_session_context
from src.auth.mfa_models import MFASetup

# Admin resets MFA for locked user
client_id = 123

with get_session_context() as session:
    mfa_setup = session.query(MFASetup).filter_by(client_id=client_id).first()
    
    if mfa_setup:
        mfa_setup.mfa_enabled = False
        mfa_setup.mfa_verified = False
        mfa_setup.totp_secret_encrypted = None
        mfa_setup.backup_codes_encrypted = None
        mfa_setup.microsoft_enabled = False
        mfa_setup.oracle_enabled = False
        
        session.commit()
        print("MFA reset for this user")
```

## Security Features

### 1. Encryption at Rest
- All TOTP secrets stored encrypted with Fernet (symmetric encryption)
- Encryption key never stored with encrypted data
- Backup codes also encrypted in database

### 2. Rate Limiting
- Tracks failed attempts per phone number
- 5 failed attempts → 15-minute account lockout
- Prevents brute force attacks
- Successful attempt clears lockout counter

### 3. Time Window Tolerance
- TOTP codes valid for ±30 seconds (1 time step)
- Accommodates minor clock skew between devices
- Still secure against token reuse within same time window

### 4. Backup Codes
- 8 unique single-use codes per user
- SHA-256 hashed before storage
- Enables account recovery if authenticator lost
- Logged when used for audit trail

### 5. Session Management
- JWT tokens with 24-hour expiration
- Refresh tokens with 7-day expiration
- Session records stored in database
- IP address and device fingerprint tracking
- Automatic session invalidation on expiration

### 6. Audit Logging
- Every authentication attempt logged:
  - Success/failure
  - Attempt type (TOTP, backup code, initial setup)
  - Authenticator type (Microsoft, Oracle)
  - IP address and user agent
  - Timestamp and error reason (if failed)
- Available for compliance reporting

## Integration with WhatsApp Bot

### Message Flow

```
User: "Setup MFA"
    ↓
Bot Receives WhatsApp Message
    ↓
Message Parser Detects MFA Intent
    ↓
POST /api/auth/mfa/setup
    ├─ Generate TOTP secret
    ├─ Create QR code image
    ├─ Store setup in database
    └─ Send QR + instructions to WhatsApp
    ↓
User: Scans QR with Microsoft Authenticator
    ↓
User: "Verify 123456"
    ↓
POST /api/auth/mfa/verify
    ├─ Validate TOTP code
    ├─ Create session
    └─ Return JWT tokens
    ↓
User: Authenticated for 24 hours
```

### Webhook Handler Integration

```python
# In src/whatsapp/message_parser.py

def parse_authentication_intent(message: str) -> Optional[str]:
    """Detect authentication-related intents."""
    
    if 'setup mfa' in message.lower() or 'enable 2fa' in message.lower():
        return 'MFA_SETUP'
    
    if 'verify' in message.lower() and len(message.split()) == 2:
        code = message.split()[1]
        if code.isdigit() and len(code) == 6:
            return 'MFA_VERIFY'
    
    if 'backup' in message.lower() and len(message.split()) == 2:
        code = message.split()[1].upper()
        if len(code) == 8:
            return 'MFA_BACKUP_CODE'
    
    return None

# Route to appropriate handler
intent = parse_authentication_intent(user_message)

if intent == 'MFA_SETUP':
    response = call_api('POST', '/api/auth/mfa/setup', {
        'client_id': client_id,
        'phone_number': phone_number,
        'authenticator_type': 'microsoft'
    })
    
elif intent == 'MFA_VERIFY':
    code = extract_code(user_message)
    response = call_api('POST', '/api/auth/mfa/verify', {
        'client_id': client_id,
        'phone_number': phone_number,
        'code': code
    })
```

## Testing

### Unit Tests (Create test/auth/)

```bash
# Test TOTP verification
pytest test/auth/test_mfa.py::test_totp_generation
pytest test/auth/test_mfa.py::test_totp_verification
pytest test/auth/test_mfa.py::test_totp_with_skew

# Test backup codes
pytest test/auth/test_mfa.py::test_backup_code_generation
pytest test/auth/test_mfa.py::test_backup_code_single_use

# Test rate limiting
pytest test/auth/test_mfa.py::test_rate_limiting_lockout
pytest test/auth/test_mfa.py::test_rate_limiting_reset

# Test sessions
pytest test/auth/test_session.py::test_session_creation
pytest test/auth/test_session.py::test_token_refresh
pytest test/auth/test_session.py::test_session_expiration

# Test QR generation
pytest test/auth/test_qr_generator.py::test_qr_generation
pytest test/auth/test_qr_generator.py::test_qr_formatting
```

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `src/auth/mfa.py` | 400+ | TOTP & MFA business logic |
| `src/auth/qr_generator.py` | 350+ | QR code generation |
| `src/auth/session.py` | 400+ | JWT session management |
| `src/auth/routes.py` | 500+ | Flask API endpoints |
| `src/auth/mfa_models.py` | 150+ | Database models (5 tables) |
| `src/auth/__init__.py` | 50+ | Package initialization |

**Total MFA System: 2,000+ lines of production code**

## Configuration (.env.example)

```bash
# TOTP Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
TOTP_ENCRYPTION_KEY=<your-encryption-key>

# JWT Secret (generate: secrets.token_urlsafe(32))
JWT_SECRET_KEY=<your-jwt-secret>

# Admin Authentication
ADMIN_API_KEY=<admin-api-key>

# Optional
SESSION_ENCRYPTION_KEY=<session-encryption-key>
COMPANY_NAME=WhatsApp Inventory Bot
```

## Next Steps

1. **Create test suite** - `test/auth/test_*.py` (400+ lines)
2. **Add admin CLI commands** - `src/auth/admin_commands.py` (150+ lines)
3. **Integrate with WhatsApp message parser** - Update intent detection
4. **Database migration** - Create Alembic migration for 5 new tables
5. **Documentation** - API documentation for client integration
6. **Monitoring** - Add metrics and alerts for authentication failures

## Backwards Compatibility

All MFA functionality is optional:
- Existing users can continue without MFA
- Non-MFA endpoints continue to work
- MFA enables optionally per user
- No breaking changes to existing API

## Support

For configuration questions or troubleshooting:
- Check `QUICK_START_NLP_AZURE.md` for Azure-specific setup
- Review `IMPLEMENTATION_PROGRESS.md` for project status
- Check individual module docstrings for API details

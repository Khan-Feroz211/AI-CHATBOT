# ✅ WhatsApp Inventory Bot - Deployment Checklist

Complete this checklist to ensure your bot is production-ready.

---

## PART 1: Code & Dependencies ✓

### Installation
- [ ] Python 3.11+ installed: `python --version`
- [ ] Virtual environment created: `python -m venv venv`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] No import errors: `python -c "import src.main"`
- [ ] SQLAlchemy upgraded: `pip install --upgrade SQLAlchemy`

### Code Quality
- [ ] No syntax errors: `python -m py_compile src/**/*.py`
- [ ] Code formatted: `black src/`
- [ ] Linting passed: `flake8 src/`
- [ ] Type checking passed: `mypy src/`

### Database
- [ ] Database models created: `python -c "from src.core.models import Client; print(Client.__tablename__)"`
- [ ] Migrations applied (if using Alembic)
- [ ] Database connection working: `psql -U user -d database -c "SELECT 1"`

---

## PART 2: Local Testing ✓

### Services Running
- [ ] Bot starts without errors: `python run.py`
- [ ] Health endpoint responds: `curl http://localhost:5000/health`
- [ ] Web interface accessible: `curl -s http://localhost:5000/health | jq`

### Unit Tests
- [ ] Tests collect without errors: `pytest tests/ --collect-only`
- [ ] Auth tests pass: `pytest tests/test_auth.py -v`
- [ ] Security tests pass: `pytest tests/test_security.py -v`
- [ ] Coverage > 80%: `pytest tests/ --cov=src`

### Integration Tests
- [ ] Health check passes: `pytest tests/ -k health -v`
- [ ] Webhook verification works: `pytest tests/test_whatsapp.py::test_whatsapp_webhook_challenge -v`
- [ ] Message parsing works: `pytest tests/test_whatsapp.py -v`

### Local Bot Testing
```bash
# Run local test suite
python test_local.py
```

- [ ] Health check: ✅ PASS
- [ ] Webhook verification: ✅ PASS
- [ ] Text message: ✅ PASS
- [ ] MFA setup: ✅ PASS
- [ ] Stock command: ✅ PASS
- [ ] Order command: ✅ PASS

---

## PART 3: Configuration ✓

### Environment Variables
- [ ] `.env` file created from `.env.example`
- [ ] All required variables set (see table below)
- [ ] No placeholder values left (like "your-secret-here")
- [ ] Sensitive values not in code, only in `.env`
- [ ] `.env` file is in `.gitignore`

### Required Environment Variables Check

```bash
# Verify all required variables are set
python -c "
import os
required = [
    'FLASK_ENV', 'SECRET_KEY', 'DATABASE_URL',
    'WHATSAPP_PROVIDER', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN',
    'JWT_SECRET_KEY', 'TOTP_ENCRYPTION_KEY', 'ADMIN_PHONE'
]
missing = [v for v in required if not os.getenv(v)]
if missing:
    print(f'❌ Missing: {missing}')
else:
    print('✅ All required variables set')
"
```

- [ ] Output shows: ✅ All required variables set

### Configuration Validation
- [ ] Database URL is valid PostgreSQL URI
- [ ] Secret keys are 32+ characters
- [ ] Phone numbers are in E.164 format (+country-code-number)
- [ ] WhatsApp provider is either 'twilio' or 'meta'
- [ ] MFA_ISSUER is set to company name

---

## PART 4: Webhook Setup (CRITICAL) ✓

### Twilio Webhook (if using Twilio)
- [ ] Twilio account created and verified
- [ ] WhatsApp Sandbox set up
- [ ] Credentials copied to `.env`:
  - [ ] TWILIO_ACCOUNT_SID
  - [ ] TWILIO_AUTH_TOKEN
  - [ ] TWILIO_PHONE_NUMBER
- [ ] Webhook URL registered in Twilio Console
- [ ] Webhook verification successful

### Meta Webhook (if using Meta)
- [ ] Meta Developer account created
- [ ] WhatsApp Business Account linked
- [ ] Credentials copied to `.env`:
  - [ ] META_ACCESS_TOKEN
  - [ ] META_PHONE_NUMBER_ID
  - [ ] META_WEBHOOK_VERIFY_TOKEN
  - [ ] META_APP_SECRET
- [ ] Webhook URL registered in Meta App Dashboard
- [ ] Webhook verification token verified
- [ ] Subscribed to required webhook fields:
  - [ ] messages
  - [ ] message_status

### Webhook Testing
```bash
# Test webhook verification
curl -X GET "http://localhost:5000/webhook" \
  -d "hub.mode=subscribe" \
  -d "hub.verify_token=$VERIFY_TOKEN" \
  -d "hub.challenge=test_123"

# Test incoming message (curl should show 200 OK)
```

- [ ] Webhook verification returns challenge
- [ ] Webhook accepts POST messages with 200 OK
- [ ] Bot logs show message receipt

### End-to-End Message Flow
```bash
# Send test message from WhatsApp
# Bot should respond within 5 seconds
```

- [ ] Message sent from WhatsApp
- [ ] Bot receives message in logs
- [ ] Bot sends reply automatically
- [ ] Reply received in WhatsApp < 5 seconds

---

## PART 5: MFA/2FA Testing ✓

### MFA Setup Flow
```bash
# Test the full MFA setup sequence
# 1. Message: "setup mfa"
# 2. Receive QR code
# 3. Scan with Authenticator app
# 4. Message 6-digit code
# 5. Receive confirmation
```

- [ ] "setup mfa" message triggers QR code generation
- [ ] QR code image sent via WhatsApp
- [ ] QR code scans correctly in Microsoft/Google Authenticator
- [ ] 6-digit code verified successfully
- [ ] Backup codes generated and received
- [ ] User can store backup codes

### MFA Security Testing
```bash
# Test rate limiting after 5 failed attempts
# Test 15-minute lockout
# Test backup code single-use enforcement
```

- [ ] Rate limiting works: 5 failed attempts → locked
- [ ] Lockout duration is 15 minutes
- [ ] Lockout message sent to user
- [ ] Admin notified of lockout attempt
- [ ] Backup codes work as fallback
- [ ] Backup codes are single-use only

---

## PART 6: Bot Functionality Testing ✓

### Stock Management
```bash
# Message: "stock"
# Message: "stock iphone" 
# Message: "low stock"
```

- [ ] "stock" returns full inventory
- [ ] "stock [item]" returns specific item
- [ ] Low stock items highlighted
- [ ] Stock numbers accurate in database

### Order Management
```bash
# Message: "order"
# Follow ordering flow
# Complete order
```

- [ ] "order" starts ordering flow
- [ ] Customer can browse items
- [ ] Customer can add to cart
- [ ] Quantities validated (positive, in stock)
- [ ] Order total calculated correctly
- [ ] Order confirmation sent
- [ ] Order stored in database
- [ ] Admin receives order notification

### Transaction Recording
```bash
# Check database for order transactions
```

- [ ] Order appears in transactions table
- [ ] Transaction timestamp is accurate
- [ ] Amount is correct
- [ ] Customer phone number recorded
- [ ] Order status tracking works

### Authentication Flow
```bash
# New customer interaction
```

- [ ] First-time customer creates account
- [ ] MFA can be set up optionally
- [ ] Access persists across sessions
- [ ] Admin can revoke access if needed

---

## PART 7: Performance & Security ✓

### Performance Metrics
```bash
# Test response times
time curl http://localhost:5000/health
```

- [ ] Health check < 100ms
- [ ] Message processing < 2 seconds
- [ ] Database queries optimized
- [ ] No N+1 query problems
- [ ] Bot handles 10+ concurrent users

### Security Audit
- [ ] All secrets in environment variables
- [ ] No hardcoded passwords or API keys
- [ ] HTTPS/SSL required in production
- [ ] CORS properly configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (using SQLAlchemy ORM)
- [ ] Rate limiting enabled
- [ ] Admin API key protected
- [ ] Database user has minimal permissions
- [ ] Logs don't contain sensitive data

### Database Security
- [ ] Database user (not root) for connection
- [ ] Database password is strong (12+ chars, mixed)
- [ ] Database backups scheduled daily
- [ ] Backup encryption enabled
- [ ] Backup retention policy set (30 days)
- [ ] Point-in-time recovery tested

---

## PART 8: Deployment Readiness ✓

### Docker Readiness
```bash
# Test Docker image
docker build -t test-bot:latest .
docker run -p 5000:5000 --env-file .env test-bot:latest
curl http://localhost:5000/health
```

- [ ] Dockerfile builds successfully
- [ ] Image runs without errors
- [ ] Health check passes in container
- [ ] Logs visible with `docker logs`

### Docker Compose
```bash
docker-compose up -d
docker-compose ps  # All services "Up" and "healthy"
```

- [ ] All services (bot, db, redis) running
- [ ] Health checks all passing
- [ ] No port conflicts
- [ ] Logs show no errors
- [ ] Database initialized in PostgreSQL
- [ ] Shutdown gracefully: `docker-compose down`

### Cloud Deployment Preparation
- [ ] Dockerfile ready (tested locally)
- [ ] docker-compose.yml ready (tested locally)
- [ ] railway.toml created (if using Railway)
- [ ] render.yaml created (if using Render)
- [ ] Environment variable secrets prepared
- [ ] Domain/DNS configured
- [ ] SSL certificate ready

---

## PART 9: Post-Deployment Verification ✓

### Health Checks
```bash
# After deploying to production
curl https://your-domain.com/health
```

- [ ] Production server is reachable
- [ ] Health endpoint responds 200 OK
- [ ] Response time < 500ms
- [ ] SSL certificate valid

### Webhook Verification
```bash
# Send test message from WhatsApp account
```

- [ ] Test message received by bot
- [ ] Bot processes message
- [ ] Response sent back
- [ ] Message appears in bot logs

### Database Connectivity
```bash
# Verify production database connection
```

- [ ] Database is online
- [ ] Connection successful
- [ ] Tables created and populated
- [ ] Transactions recording properly

### Monitoring Setup
- [ ] Error tracking configured (Sentry/Datadog)
- [ ] Uptime monitoring configured (UptimeRobot)
- [ ] Log aggregation working (CloudWatch/ELK)
- [ ] Alerts configured for critical errors
- [ ] Alerts configured for high response times

---

## PART 10: User Acceptance Testing ✓

### Employee Testing
```
Have team members test the bot as actual users
```

- [ ] 5+ employees tested the bot
- [ ] All basic flows work smoothly
- [ ] Response times acceptable
- [ ] MFA setup is intuitive
- [ ] Error messages are helpful
- [ ] No crashes or 500 errors

### Stakeholder Sign-Off
- [ ] Product manager: Approved functionality
- [ ] Security team: Approved security implementation
- [ ] Ops team: Approved deployment process
- [ ] Finance: Approved resource usage
- [ ] Management: Approved for production launch

---

## PART 11: Final Pre-Launch ✓

### Documentation
- [ ] User guide created and distributed
- [ ] Admin guide created
- [ ] Deployment guide updated
- [ ] API documentation complete
- [ ] Troubleshooting guide available

### Backups & Disaster Recovery
- [ ] Database backup created
- [ ] Backup tested for restoration
- [ ] Backup storage location documented
- [ ] Recovery procedure documented
- [ ] RTO/RPO targets defined

### Support Plan
- [ ] Support channel established (Slack/email)
- [ ] Escalation procedure documented
- [ ] On-call schedule created for weekends/nights
- [ ] Known issues list maintained
- [ ] Bug reporting process established

### Go-Live Handoff
- [ ] All documentation handed to team
- [ ] Access credentials distributed securely
- [ ] Team trained on operations
- [ ] Monitoring dashboards shared
- [ ] Incident response plan reviewed

---

## SIGN-OFF

**Verification Completed By:** _____________________ Date: __________

**System Ready for Production:** ☐ YES ☐ NO

**Comments/Issues:**
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

**Action Items (if not ready):**
1. ___________________________________________________________
2. ___________________________________________________________
3. ___________________________________________________________

---

## Post-Launch Monitoring (First 24 Hours)

- [ ] Monitor error rate (should be < 0.1%)
- [ ] Monitor response times (should be < 2 sec)
- [ ] Check message delivery success rate (> 99%)
- [ ] Verify MFA users can authenticate
- [ ] Monitor database performance
- [ ] Check for any user complaints
- [ ] Review webhook logs for failures
- [ ] Confirm automated backups ran
- [ ] Test failover procedures
- [ ] Update status page for public visibility

---

## Continuous Monitoring (Ongoing)

**Weekly:**
- [ ] Review error logs and fix issues
- [ ] Check database size growth
- [ ] Review performance metrics
- [ ] Update documentation as needed

**Monthly:**
- [ ] Security audit (check for vulnerabilities)
- [ ] Backup restoration test
- [ ] Performance optimization review
- [ ] Update dependencies for security patches

**Quarterly:**
- [ ] Capacity planning review
- [ ] Disaster recovery drill
- [ ] Security assessment
- [ ] User feedback collection

---

**Status:** 
- 🟢 READY FOR PRODUCTION (All items checked)
- 🟡 IN PROGRESS (Some items pending)
- 🔴 NOT READY (Critical items missing)

**Next Review Date:** ______________

---

**Contact for Questions:** 
- Technical Lead: _____________________ 
- Operations: _____________________
- Security: _____________________

# 🤝 Contributing Guide

Thank you for interest in contributing! This guide explains our development process and standards.

## Code of Conduct

Be respectful, inclusive, and professional. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).

---

## Getting Started

### 1. Fork & Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR-USERNAME/project-assistant-bot.git
cd project-assistant-bot
git remote add upstream https://github.com/Khan-Feroz211/project-assistant-bot.git
```

### 2. Create Feature Branch

```bash
git checkout -b feature/amazing-feature
# or for bugfixes:
git checkout -b fix/bug-description
```

### 3. Setup Development Environment

```bash
python -m venv .venv311
source .venv311/bin/activate  # or .venv311\Scripts\activate on Windows

pip install -r requirements.txt
```

---

## Development Standards

### Code Style

**Python Style**: PEP 8 using Black formatter

```bash
black src/
flake8 src/
```

**Maximum line length**: 88 characters (Black default)

**Naming conventions**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private methods: `_private_method()`

### Type Hints

All functions should have type hints:

```python
# ❌ Bad
def get_user(id):
    return db.query(User).filter(User.id == id).first()

# ✅ Good
def get_user(user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()
```

### Docstrings

All public functions need docstrings (Google style):

```python
def create_task(user_id: int, title: str, priority: str = "medium") -> Task:
    """Create a new task for a user.
    
    Args:
        user_id: The ID of the user creating the task
        title: The task title (max 255 characters)
        priority: Priority level: "low", "medium", "high" (default: "medium")
    
    Returns:
        The created Task object with generated ID
    
    Raises:
        ValueError: If title is empty or exceeds 255 characters
        UserNotFoundError: If user_id doesn't exist
    
    Example:
        >>> task = create_task(user_id=1, title="Implement MFA")
        >>> print(task.id, task.title)
        1 Implement MFA
    """
    if not title or len(title) > 255:
        raise ValueError("Title must be 1-255 characters")
    
    if not get_user(user_id):
        raise UserNotFoundError(f"User {user_id} not found")
    
    task = Task(user_id=user_id, title=title, priority=priority)
    db.session.add(task)
    db.session.commit()
    return task
```

---

## Testing Requirements

All contributions must include tests:

### 1. Unit Tests

```bash
pytest tests/unit/
```

Test file location: `tests/unit/test_<feature>.py`

```python
# tests/unit/test_tasks.py
import pytest
from src.services.tasks import create_task
from src.core.database import User, Task

@pytest.fixture
def user(db_session):
    """Create test user"""
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    return user

def test_create_task_success(user):
    """Should create task for valid user"""
    task = create_task(user_id=user.id, title="Test Task")
    
    assert task.id is not None
    assert task.title == "Test Task"
    assert task.user_id == user.id

def test_create_task_invalid_title():
    """Should raise error for empty title"""
    with pytest.raises(ValueError):
        create_task(user_id=1, title="")

def test_create_task_user_not_found():
    """Should raise error if user doesn't exist"""
    with pytest.raises(UserNotFoundError):
        create_task(user_id=99999, title="Test")
```

### 2. Integration Tests

Test API endpoints:

```bash
pytest tests/integration/
```

### 3. Run Full Test Suite

```bash
# Run all tests with coverage
pytest --cov=src --cov=api --cov-report=html

# View coverage report
open htmlcov/index.html  # or browse to it
```

**Minimum coverage**: 80% for new code

---

## Making Changes

### 1. Create Feature

```bash
# Create branch
git checkout -b feature/add-payment-analytics

# Make changes to src/services/payments.py
# Add tests to tests/unit/test_payments.py
# Add integration tests to tests/integration/test_payment_api.py

# Test locally
pytest tests/unit/test_payments.py -v
pytest tests/integration/test_payment_api.py -v
```

### 2. Commit Messages

Format: `<type>: <subject>`

**Types**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting, missing semicolons, etc.
- `refactor:` Code restructuring without behavior change
- `perf:` Performance improvements
- `test:` Adding/updating tests
- `chore:` Dependency updates, build process changes

**Examples**:
```bash
git commit -m "feat: add payment failure retry logic"
git commit -m "fix: resolve MFA verification timeout on WhatsApp"
git commit -m "docs: update API documentation for /payments endpoint"
git commit -m "test: add integration tests for payment-webhook"
```

**Message body** (optional but recommended):
```
feat: add payment failure retry logic

- Implement exponential backoff for payment gateway failures
- Add max retry count configuration (default: 3)
- Log all retry attempts for audit trail
- Send notification to user after final failure

Fixes #123
```

### 3. Keep Branch Updated

```bash
git fetch upstream
git rebase upstream/main
```

### 4. Push & Create PR

```bash
git push origin feature/add-payment-analytics
```

Then create Pull Request on GitHub.

---

## Pull Request Process

### PR Title Format
`[COMPONENT] Brief description`

Examples:
- `[API] Add payment retry mechanism`
- `[WhatsApp] Fix webhook verification timeout`
- `[MFA] Generate TOTP backup codes`

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (fixes #issue-number)
- [ ] New feature (fixes #issue-number)
- [ ] Breaking change (fixes #issue-number)
- [ ] Documentation update

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [x] Unit tests added
- [x] Integration tests added
- [x] All tests passing: `pytest`
- [x] Coverage >= 80%

## Checklist
- [x] Code follows style guidelines (`black`, `flake8`)
- [x] Docstrings added for public methods
- [x] Type hints included
- [x] Tests included and passing
- [x] Documentation updated
- [x] No new warnings in logs
- [x] Manually tested locally

## Screenshots (if applicable)
[Add screenshots/GIFs if UI changes]

## Related Issues
Fixes #123
Related to #124, #125
```

---

## Code Review Process

### What We Review

1. **Code Quality**
   - Follows PEP 8 style
   - Type hints present
   - Docstrings complete
   - No duplicate code

2. **Testing**
   - Adequate test coverage (80%+)
   - Edge cases handled
   - Error conditions tested

3. **Security**
   - No hardcoded secrets
   - SQL injection protection
   - XSS prevention
   - CSRF tokens present

4. **Documentation**
   - API docs updated
   - README changes if needed
   - Change log entry

5. **Performance**
   - No obvious optimizations missing
   - Database queries efficient
   - No memory leaks

### Review Cycle

1. **Author** submits PR
2. **Automated Checks** run (CI/CD):
   - Tests must pass
   - Coverage >= 80%
   - Linting passes
3. **Code Review** by maintainers
4. **Author** addresses feedback
5. **Approved** → merged

---

## Project Structure

Understand before making changes:

```
src/
├── api/              # REST API endpoints
├── agents/           # AI agent implementations
├── core/             # Core utilities (DB, auth, config)
├── ml/               # Machine learning pipelines
├── monitoring/       # Logging, metrics
├── rag/              # Retrieval-augmented generation
└── services/         # Business logic

tests/
├── unit/             # Fast, isolated tests
├── integration/      # API/service tests
├── e2e/              # End-to-end workflows
└── fixtures/         # Shared test data

scripts/
├── setup/            # Setup scripts
├── tools/            # Diagnostic/utility tools
└── generate/         # Code generation scripts

docs/
├── API.md            # API documentation
├── ARCHITECTURE.md   # System design
└── education/        # Learning resources
```

---

## Common Development Tasks

### Add New API Endpoint

1. **Create handler** in `src/api/routes/`:
```python
# src/api/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from src.core.auth import get_current_user
from src.services.analytics import get_user_stats

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/stats")
async def get_stats(user = Depends(get_current_user)):
    """Get user analytics statistics"""
    stats = get_user_stats(user.id)
    return stats
```

2. **Register in main app** in `src/api/main.py`:
```python
from src.api.routes import analytics

app.include_router(analytics.router)
```

3. **Write tests** in `tests/integration/test_analytics.py`:
```python
async def test_get_stats_authenticated():
    response = client.get("/api/v1/analytics/stats", headers=auth_headers)
    assert response.status_code == 200
    assert "tasks_completed" in response.json()
```

### Add New Service

1. **Create service** in `src/services/`:
```python
# src/services/export.py
class ExportService:
    """Handle task export in various formats"""
    
    def export_csv(self, user_id: int) -> bytes:
        """Export user tasks as CSV"""
        tasks = get_user_tasks(user_id)
        # CSV export logic
        return csv_bytes
```

2. **Write unit tests** in `tests/unit/test_export.py`:
```python
def test_export_csv(user):
    service = ExportService()
    csv_data = service.export_csv(user.id)
    assert b"task_id,title" in csv_data
```

### Add Database Migration

1. **Create migration file**:
```bash
# Using Alembic (if available)
alembic revision --autogenerate -m "add_export_format_column"
```

2. **Or SQLite migration**:
```python
# scripts/tools/migration_add_export_format.py
def migrate():
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE tasks ADD COLUMN export_format TEXT DEFAULT 'json'")
    conn.commit()
```

---

## Performance Guidelines

### Query Optimization

```python
# ❌ N+1 query problem
users = get_all_users()
for user in users:
    tasks = user.tasks  # Query triggered for each user!

# ✅ Eager loading
users = get_all_users(join_tasks=True)
for user in users:
    tasks = user.tasks  # Already loaded
```

### Caching

```python
# Use Redis for frequently accessed data
from src.core.cache import cache

@cache(ttl=3600)  # Cache for 1 hour
def get_user_stats(user_id: int):
    return compute_expensive_stats(user_id)
```

### Batch Operations

```python
# ❌ Slow: Multiple inserts
for item in items:
    db.session.add(item)
    db.session.commit()

# ✅ Fast: Single batch insert
db.session.add_all(items)
db.session.commit()
```

---

## Troubleshooting

### Tests Failing Locally

```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Check database
python scripts/tools/migrate_database.py

# Rebuild test database
pytest --tb=short tests/unit/test_something.py -v
```

### Import Errors

```bash
# Ensure venv is activated
source .venv311/bin/activate

# Verify PYTHONPATH
echo $PYTHONPATH

# Reinstall editable
pip install -e .
```

### Merge Conflicts

```bash
# Rebase from main
git fetch upstream
git rebase upstream/main

# Resolve conflicts in editor, then:
git add .
git rebase --continue
```

---

## Resources

- [Python PEP 8 Style Guide](https://pep8.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Git Workflow Guide](https://git-scm.com/book/en/v2)

---

## Questions?

- **GitHub Issues**: Discuss features or bugs
- **GitHub Discussions**: Ask questions
- **Email**: khan.feroz211@gmail.com

Thank you for contributing! 🎉


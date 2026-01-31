# Contributing to CyberShield DLP Security System

Thank you for your interest in contributing to CyberShield! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Screenshots** (if applicable)
- **Environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide detailed description** of the proposed feature
- **Explain why this enhancement would be useful**
- **List any alternatives** you've considered

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`: `git checkout -b feature/your-feature-name`
3. **Make your changes** following our coding standards
4. **Test your changes** thoroughly
5. **Commit** with clear messages: `git commit -m "Add feature: description"`
6. **Push** to your fork: `git push origin feature/your-feature-name`
7. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/MyCyber-Project.git
cd MyCyber-Project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

## Coding Standards

### Python Style Guide

- Follow **PEP 8** style guide
- Use **4 spaces** for indentation (no tabs)
- Maximum line length: **88 characters** (Black formatter)
- Use **meaningful variable names**
- Add **docstrings** to functions and classes

### Code Example

```python
def scan_data(content: str, policy_id: int) -> dict:
    """
    Scan content against specified DLP policy.
    
    Args:
        content: The content to scan
        policy_id: ID of the policy to apply
        
    Returns:
        Dictionary containing scan results and violations
        
    Raises:
        PolicyNotFoundError: If policy_id doesn't exist
    """
    # Implementation here
    pass
```

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Move cursor to..." not "Moves cursor to..."
- Limit first line to 72 characters
- Reference issues: "Fix #123: Description"

Examples:
```
Add user authentication module
Fix security vulnerability in data scanner
Update README with installation instructions
Refactor policy management code
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_auth.py

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

### Writing Tests

- Write tests for all new features
- Maintain test coverage above 80%
- Use descriptive test names
- Follow AAA pattern: Arrange, Act, Assert

```python
def test_user_authentication_success():
    # Arrange
    username = "testuser"
    password = "testpass123"
    
    # Act
    result = authenticate_user(username, password)
    
    # Assert
    assert result.success is True
    assert result.user.username == username
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update API documentation if applicable
- Include code comments for complex logic

## Security

### Reporting Security Issues

**DO NOT** create public issues for security vulnerabilities.

Email security concerns to: **www.ferozkhan@outlook.com**

### Security Guidelines

- Never commit sensitive data (passwords, API keys)
- Use environment variables for configuration
- Validate all user inputs
- Follow OWASP security practices
- Use parameterized queries

## Code Review Process

1. **Automated checks** must pass (linting, tests)
2. **Maintainer review** required
3. **Address feedback** and update PR
4. **Approval** from at least one maintainer
5. **Merge** after all checks pass

## Questions?

Feel free to:
- Open an issue for questions
- Email the team at www.ferozkhan@outlook.com
- Join our community discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to CyberShield! 🛡️

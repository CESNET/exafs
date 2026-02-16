# CLAUDE.md - AI Assistant Guide for ExaFS

## Project Overview

**ExaFS** is a Flask-based web application for managing ExaBGP (Border Gateway Protocol) rules to prevent DDoS and other malicious cyber attacks. It provides a user interface and REST API for creating, validating, and executing BGP FlowSpec and RTBH (Remotely Triggered Black Hole) rules.

- **Current Version**: 1.1.9
- **License**: MIT
- **Primary Language**: Python (3.9+)
- **Framework**: Flask
- **Organization**: CESNET (Czech national e-infrastructure for science, research and education)
- **PyPI Package**: `exafs`
- **Total Lines of Code**: ~11,500 lines

## Key Features

1. **User Authorization**: Role-based access control for BGP rule management
2. **Validation System**: Syntax and access rights validation before rule storage
3. **Rule Types**: IPv4 FlowSpec, IPv6 FlowSpec, and RTBH rules
4. **Authentication Methods**: SSO (Shibboleth), HTTP Header Auth, or Local Auth
5. **REST API**: Swagger-documented API with token-based authentication
6. **Rule Persistence**: Database storage with automatic restoration after system reboot
7. **Whitelist System**: Automated rule creation from whitelists

## Repository Structure

```
exafs/
├── flowapp/                    # Main application package
│   ├── __init__.py            # Flask app factory
│   ├── __about__.py           # Version and metadata
│   ├── auth.py                # Authentication decorators
│   ├── constants.py           # Application constants
│   ├── flowspec.py            # FlowSpec rule translation logic
│   ├── validators.py          # Form and data validators
│   ├── messages.py            # User-facing messages
│   ├── output.py              # ExaBGP output formatting
│   ├── instance_config.py     # Default dashboard configuration
│   │
│   ├── models/                # SQLAlchemy database models
│   │   ├── __init__.py        # Model exports
│   │   ├── base.py            # Base models and relationships
│   │   ├── user.py            # User and Role models
│   │   ├── organization.py    # Organization model
│   │   ├── api.py             # API key models
│   │   ├── community.py       # BGP Community models
│   │   ├── log.py             # Audit log model
│   │   ├── utils.py           # Model utility functions
│   │   └── rules/             # Rule-specific models
│   │       ├── flowspec.py    # IPv4/IPv6 FlowSpec models
│   │       ├── rtbh.py        # RTBH model
│   │       ├── whitelist.py   # Whitelist models
│   │       └── base.py        # Base rule models
│   │
│   ├── forms/                 # WTForms form definitions
│   │   ├── base.py            # Base form classes
│   │   ├── user.py            # User management forms
│   │   ├── organization.py    # Organization forms
│   │   ├── api.py             # API key forms
│   │   ├── choices.py         # Form choice generators
│   │   └── rules/             # Rule-specific forms
│   │       ├── ipv4.py        # IPv4 FlowSpec forms
│   │       ├── ipv6.py        # IPv6 FlowSpec forms
│   │       ├── rtbh.py        # RTBH forms
│   │       └── whitelist.py   # Whitelist forms
│   │
│   ├── views/                 # Flask Blueprints (routes)
│   │   ├── __init__.py        # Blueprint registration
│   │   ├── dashboard.py       # Main dashboard views
│   │   ├── rules.py           # Rule CRUD operations
│   │   ├── whitelist.py       # Whitelist management
│   │   ├── admin.py           # Admin operations
│   │   ├── api_keys.py        # API key management
│   │   ├── api_v1.py          # API v1 endpoints (deprecated)
│   │   ├── api_v2.py          # API v2 endpoints
│   │   ├── api_v3.py          # API v3 endpoints (current)
│   │   └── api_common.py      # Common API utilities
│   │
│   ├── services/              # Business logic layer
│   │   ├── base.py            # Base service classes
│   │   ├── rule_service.py    # Rule creation/modification logic
│   │   ├── whitelist_service.py # Whitelist rule generation
│   │   └── whitelist_common.py  # Whitelist utilities
│   │
│   ├── utils/                 # Utility functions
│   │   └── [various utilities]
│   │
│   ├── templates/             # Jinja2 templates
│   │   ├── layouts/           # Base layouts
│   │   ├── pages/             # Page templates
│   │   ├── forms/             # Form templates
│   │   └── errors/            # Error pages
│   │
│   ├── static/                # Static assets
│   │   ├── js/                # JavaScript files
│   │   └── swagger.yml        # Swagger API specification
│   │
│   └── tests/                 # Test suite
│       ├── test_flowapp.py    # Basic app tests
│       ├── test_models.py     # Model tests
│       ├── test_forms.py      # Form validation tests
│       ├── test_validators.py # Validator tests
│       ├── test_flowspec.py   # FlowSpec translation tests
│       ├── test_api_*.py      # API endpoint tests
│       ├── test_rule_service.py # Service layer tests
│       └── test_whitelist_*.py  # Whitelist tests
│
├── docs/                      # Documentation
│   ├── INSTALL.md            # Installation guide
│   ├── API.md                # API documentation
│   ├── AUTH.md               # Authentication setup
│   ├── DB_*.md               # Database guides
│   └── guarda-service/       # Rule restoration service docs
│
├── config.example.py         # Configuration template
├── instance_config_override.example.py # Dashboard override template
├── run.example.py            # Application run script template
├── db-init.py                # Database initialization (runs flask db upgrade)
├── scripts/
│   └── migrate_v0x_to_v1.py  # Optional v0.x to v1.0+ migration helper
├── pyproject.toml            # Project metadata and dependencies
├── setup.cfg                 # Setup configuration
├── CHANGELOG.md              # Version history
└── README.md                 # Project documentation
```

## Technology Stack

### Core Dependencies
- **Flask** (>=2.0.2) - Web framework
- **Flask-SQLAlchemy** (>=2.2) - ORM
- **Flask-Migrate** (>=3.0.0) - Database migrations
- **Flask-WTF** (>=1.0.0) - Form handling with CSRF protection
- **Flask-SSO** (>=0.4.0) - Shibboleth authentication
- **Flask-Session** - Server-side sessions
- **PyJWT** (>=2.4.0) - JWT token authentication for API
- **PyMySQL** (>=1.0.0) - MySQL database driver
- **Flasgger** - Swagger API documentation
- **Pika** (>=1.3.0) - RabbitMQ client
- **Loguru** - Logging
- **Babel** (>=2.7.0) - Internationalization

### Development Dependencies
- **pytest** (>=7.0.0) - Testing framework
- **flake8** - Code linting

### Supported Python Versions
- Python 3.9, 3.10, 3.11, 3.12, 3.13

### Database
- **Primary**: MariaDB/MySQL
- **Supported**: Any SQLAlchemy-compatible database

## Application Architecture

### MVC Pattern
The application follows a structured MVC pattern:

1. **Models** (`flowapp/models/`) - SQLAlchemy ORM models
2. **Views** (`flowapp/views/`) - Flask Blueprints handling routes
3. **Forms** (`flowapp/forms/`) - WTForms for validation
4. **Services** (`flowapp/services/`) - Business logic layer

### Key Design Patterns

1. **Factory Pattern**: App creation via `create_app()` function
2. **Blueprint Pattern**: Modular route organization
3. **Service Layer**: Business logic separated from views
4. **Validator Pattern**: Custom validators for BGP rule syntax
5. **Repository Pattern**: Model utility functions for data access

### Authentication Flow

1. **SSO Auth** (Production): Shibboleth authentication via Flask-SSO
2. **Header Auth**: External authentication via HTTP headers
3. **Local Auth** (Development): Direct UUID-based authentication
4. **API Auth**: JWT token-based authentication

## Database Models

### Core Models

#### User Management
- **User**: User accounts with UUID
- **Role**: User roles (admin, user, api_only, etc.)
- **Organization**: Network organizations
- **user_role**: Many-to-many relationship table
- **user_organization**: Many-to-many relationship table

#### Rule Models
- **Flowspec4**: IPv4 FlowSpec rules
- **Flowspec6**: IPv6 FlowSpec rules
- **RTBH**: Remotely Triggered Black Hole rules
- **Rstate**: Rule states (active, expired, etc.)
- **Action**: BGP actions (rate-limit, discard, etc.)

#### Supporting Models
- **Community**: BGP communities
- **ASPath**: AS path configurations
- **Whitelist**: Automated rule templates
- **RuleWhitelistCache**: Whitelist-generated rule tracking
- **Log**: Audit logging
- **ApiKey**: API authentication tokens
- **MachineApiKey**: Machine-to-machine API keys

### Important Model Relationships

```python
# Users belong to multiple organizations
User.organization -> Organization (many-to-many via user_organization)

# Users have multiple roles
User.roles -> Role (many-to-many via user_role)

# Rules belong to creators and organizations
Flowspec4.creator_id -> User.id
Flowspec4.organization_id -> Organization.id

# Rules can originate from whitelists
Flowspec4.whitelist_id -> Whitelist.id (nullable)
```

## Configuration

### Configuration Hierarchy

1. **Base Config** (`config.py:Config`) - Default settings
2. **Environment Config** (Production/Development/Testing classes)
3. **Instance Config** (`flowapp/instance_config.py`) - Dashboard configuration
4. **Instance Override** (`instance/config_override.py`) - Local overrides

### Critical Configuration Options

```python
# Authentication method (choose one)
SSO_AUTH = False          # Shibboleth SSO
HEADER_AUTH = False       # HTTP header auth
LOCAL_AUTH = False        # Local development auth

# Database connection
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://user:pass@host/db"

# ExaBGP API method
EXA_API = "RABBIT"        # or "HTTP"
EXA_API_RABBIT_HOST = "hostname"
EXA_API_RABBIT_PORT = 5672

# Security
JWT_SECRET = "random-secret"
SECRET_KEY = "random-secret"

# BGP Configuration
USE_RD = True             # Route Distinguisher
RD_STRING = "7654:3210"
RD_LABEL = "label"

# Rule limits
FLOWSPEC4_MAX_RULES = 9000
FLOWSPEC6_MAX_RULES = 9000
RTBH_MAX_RULES = 100000

# Rule expiration
EXPIRATION_THRESHOLD = 30  # days
```

## Development Workflow

### Initial Setup

```bash
# Clone repository
git clone https://github.com/CESNET/exafs.git
cd exafs

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .[dev]

# Copy configuration templates
cp config.example.py config.py
cp run.example.py run.py

# Edit config.py with database credentials and settings

# Initialize database (runs flask db upgrade)
python db-init.py

# Run tests
pytest

# Run development server
python run.py
```

### Database Migrations

Migration files are tracked in `migrations/versions/` and committed to git.

```bash
# Create a new migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade

# For existing databases adopting migrations for the first time
flask db stamp 001_baseline
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest flowapp/tests/test_models.py

# Run with coverage
pytest --cov=flowapp

# Run specific test
pytest flowapp/tests/test_models.py::test_user_creation -v
```

## Code Conventions

### Python Style
- Follow PEP 8 guidelines
- Maximum line length: 127 characters
- Use flake8 for linting
- Docstrings for complex functions

### Import Organization
```python
# Standard library imports
import os
from datetime import datetime

# Third-party imports
from flask import Flask, render_template
from sqlalchemy import Column, Integer

# Local imports
from flowapp.models import User
from .validators import validate_ipv4
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `Flowspec4`, `RuleService`)
- **Functions/Methods**: snake_case (e.g., `create_rule`, `validate_form`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_PORT`, `IPV4_PROTOCOL`)
- **Private Methods**: Leading underscore (e.g., `_validate_internal`)

### Model Conventions
- All models inherit from `db.Model`
- Use `__tablename__` explicitly
- Include `__repr__` for debugging
- Use type hints where helpful

### Form Conventions
- Forms inherit from `FlaskForm` or custom base classes
- Validators defined in field constructors
- Custom validators in `flowapp/validators.py`
- Form choices generated dynamically in `forms/choices.py`

### View (Blueprint) Conventions
- One blueprint per functional area
- Use `@auth_required` decorator for protected routes
- Return tuples for status codes: `return render_template(...), 404`
- JSON responses use `jsonify()`

### Service Layer Conventions
- Business logic goes in services, not views
- Services work with models and return results
- Raise exceptions for error cases
- Use database transactions appropriately

## Testing Patterns

### Test Structure
```python
def test_feature_name(client):
    """Test description"""
    # Arrange - set up test data

    # Act - perform the action
    response = client.get('/endpoint')

    # Assert - verify results
    assert response.status_code == 200
```

### Common Test Fixtures
- `client`: Unauthenticated Flask test client
- `auth_client`: Authenticated Flask test client
- `app`: Flask application instance
- Database is reset between tests

### Test File Naming
- Prefix with `test_`: `test_models.py`, `test_api_v3.py`
- Group related tests in classes
- Use descriptive test names

## Important Modules and Their Purposes

### `flowapp/flowspec.py`
Translates human-readable rule strings to ExaBGP command format.

**Key Functions:**
- `translate_sequence()`: Convert port/packet sequences to ExaBGP format
- `to_exabgp_string()`: Translate form strings to FlowSpec values
- `check_limit()`: Validate values are within acceptable ranges

### `flowapp/validators.py`
Custom validators for forms and data.

**Key Validators:**
- IP address validation (IPv4/IPv6)
- Network prefix validation
- Port and packet length validation
- BGP-specific syntax validation

### `flowapp/output.py`
Generates ExaBGP commands from rule models.

**Key Functions:**
- Format announce/withdraw messages
- Build complete BGP commands
- Handle different rule types

### `flowapp/auth.py`
Authentication and authorization.

**Key Decorators:**
- `@auth_required`: Require authentication
- `@role_required(role)`: Require specific role
- Functions to check rule modification permissions

### `flowapp/services/rule_service.py`
Core business logic for rule management.

**Key Functions:**
- `create_rule()`: Create new rules with validation
- `update_rule()`: Modify existing rules
- `delete_rule()`: Remove rules
- `reactivate_rule()`: Restore expired rules
- Rule state management

### `flowapp/models/utils.py`
Helper functions for working with models.

**Key Functions:**
- `get_user_nets()`: Get networks user can access
- `check_rule_limit()`: Verify rule count limits
- `get_user_rules_ids()`: Get rule IDs for user
- `insert_users()`: Bulk user creation

## API Structure

### API Versions
- **API v1** (`/api/v1/*`) - Deprecated, minimal maintenance
- **API v2** (`/api/v2/*`) - Legacy, still supported
- **API v3** (`/api/v3/*`) - Current, recommended version

### API Authentication
All API endpoints require JWT token authentication via `Authorization` header:
```
Authorization: Bearer <jwt-token>
```

### API Documentation
- **Local**: `/apidocs/` (Swagger UI when app is running)
- **Spec**: `flowapp/static/swagger.yml`
- **External**: [Apiary](https://exafs.docs.apiary.io/)

### Key API Endpoints (v3)
- `GET /api/v3/rules/{type}` - List rules
- `POST /api/v3/rules/{type}` - Create rule
- `PUT /api/v3/rules/{type}/{id}` - Update rule
- `DELETE /api/v3/rules/{type}/{id}` - Delete rule
- `GET /api/v3/whitelist` - List whitelists
- `POST /rules/announce_all` - Re-announce all rules (localhost only)

## Common Development Tasks

### Adding a New Rule Field

1. **Update Model** (`flowapp/models/rules/*.py`)
   ```python
   new_field = db.Column(db.String(100), nullable=True)
   ```

2. **Create Migration**
   ```bash
   flask db migrate -m "Add new_field to Flowspec4"
   flask db upgrade
   ```

3. **Update Form** (`flowapp/forms/rules/*.py`)
   ```python
   new_field = StringField('New Field', validators=[Optional()])
   ```

4. **Update Service Logic** (`flowapp/services/rule_service.py`)
   - Add field handling in create/update methods

5. **Update Output** (`flowapp/output.py`)
   - Include field in ExaBGP command generation if needed

6. **Add Tests** (`flowapp/tests/test_*.py`)
   - Test new field validation and functionality

### Adding a New API Endpoint

1. **Add Route** (`flowapp/views/api_v3.py`)
   ```python
   @api_v3.route('/endpoint', methods=['GET'])
   @jwt_required
   def new_endpoint():
       # Implementation
       return jsonify(data), 200
   ```

2. **Update Swagger** (`flowapp/static/swagger.yml`)
   - Add endpoint documentation

3. **Add Tests** (`flowapp/tests/test_api_v3.py`)
   ```python
   def test_new_endpoint(auth_client):
       response = auth_client.get('/api/v3/endpoint')
       assert response.status_code == 200
   ```

### Adding a New Validator

1. **Create Validator** (`flowapp/validators.py`)
   ```python
   def validate_something(form, field):
       if not is_valid(field.data):
           raise ValidationError('Invalid value')
   ```

2. **Use in Form** (`flowapp/forms/*.py`)
   ```python
   field_name = StringField('Label', validators=[validate_something])
   ```

3. **Add Tests** (`flowapp/tests/test_validators.py`)

## Common Pitfalls and Solutions

### Database Session Issues
**Problem**: DetachedInstanceError or stale data
**Solution**:
- Always use `db.session.commit()` after modifications
- Refresh objects after commit: `db.session.refresh(obj)`
- Use `db.session.merge()` for detached objects

### CSRF Token Issues
**Problem**: Form submissions failing with CSRF errors
**Solution**:
- Ensure `{{ form.csrf_token }}` in templates
- API endpoints should be exempt: `csrf.exempt` decorator
- Check session configuration

### Authentication Not Working
**Problem**: Users not authenticated
**Solution**:
- Verify auth method in config (SSO_AUTH/HEADER_AUTH/LOCAL_AUTH)
- Check session configuration
- Verify user exists in database with correct UUID

### Rule Limits Exceeded
**Problem**: Cannot create more rules
**Solution**:
- Check `FLOWSPEC4_MAX_RULES`, `FLOWSPEC6_MAX_RULES`, `RTBH_MAX_RULES` in config
- Use `check_rule_limit()` and `check_global_rule_limit()` before creation
- Clean up expired rules

### ExaBGP Communication Issues
**Problem**: Rules not being sent to ExaBGP
**Solution**:
- Verify `EXA_API` setting (RABBIT or HTTP)
- Check RabbitMQ connection settings
- Verify ExaBGP process is running
- Check logs for connection errors

## File Modification Guidelines

### When Modifying Models
1. ✅ **Always create a migration** after model changes
2. ✅ Update `models/__init__.py` exports if adding new models
3. ✅ Add/update `__repr__` methods for debugging
4. ✅ Update corresponding forms if fields change
5. ✅ Add tests for new fields/relationships

### When Modifying Forms
1. ✅ Add appropriate validators
2. ✅ Update corresponding templates
3. ✅ Update service layer to handle new fields
4. ✅ Add form validation tests
5. ⚠️ Don't put business logic in forms - use services

### When Modifying Views
1. ✅ Keep views thin - delegate to services
2. ✅ Use appropriate decorators (`@auth_required`, etc.)
3. ✅ Return consistent response formats
4. ✅ Add route tests
5. ⚠️ Don't query models directly - use service layer

### When Modifying Services
1. ✅ Use database transactions appropriately
2. ✅ Raise descriptive exceptions
3. ✅ Log important operations
4. ✅ Add comprehensive tests
5. ⚠️ Don't import from views - services should be independent

### When Modifying Tests
1. ✅ Follow AAA pattern (Arrange, Act, Assert)
2. ✅ Use descriptive test names
3. ✅ Clean up test data
4. ✅ Test both success and failure cases
5. ✅ Run full test suite before committing

## Security Considerations

### Authentication
- Never bypass authentication checks
- Use `@auth_required` decorator on all protected routes
- Validate JWT tokens properly in API endpoints
- Store secrets in environment variables or secure config

### Authorization
- Always check user permissions before rule modifications
- Verify user has access to organization/network
- Use `check_user_can_modify_rule()` helper
- Don't trust client-side validation alone

### Input Validation
- Validate all user inputs
- Use WTForms validators
- Sanitize data before database operations
- Validate BGP syntax before execution

### CSRF Protection
- Keep CSRF protection enabled
- Include CSRF tokens in all forms
- Exempt API endpoints appropriately

### SQL Injection Prevention
- Use SQLAlchemy ORM (parameterized queries)
- Never use raw SQL with user input
- Don't use string formatting for queries

## Logging and Debugging

### Logging
- Application uses Loguru for logging
- Logs location: `/var/log/exafs/` (production)
- Configure in `flowapp/utils/configure_logging()`

### Debug Mode
- Set `DEBUG = True` in config for development
- Shows detailed error pages
- Enables Flask debugger
- **Never enable in production**

### Common Debug Techniques
```python
# Print to logs
from loguru import logger
logger.info(f"Processing rule: {rule_id}")
logger.error(f"Failed to create rule: {error}")

# Debug in templates
{{ variable|pprint }}

# Database query debugging
from flask import current_app
current_app.config['SQLALCHEMY_ECHO'] = True
```

## Deployment Considerations

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Use strong `SECRET_KEY` and `JWT_SECRET`
- [ ] Configure production database
- [ ] Set up proper authentication (SSO or Header Auth)
- [ ] Configure HTTPS
- [ ] Set up reverse proxy
- [ ] Configure proper logging
- [ ] Set up database backups
- [ ] Configure ExaBGP connection
- [ ] Set appropriate rule limits
- [ ] Enable session security settings

### Recommended Stack
- **Web Server**: Apache with mod_proxy_uwsgi
- **WSGI Server**: uWSGI
- **Process Manager**: Supervisord
- **Database**: MariaDB
- **Auth**: Shibboleth SSO
- **Message Queue**: RabbitMQ (for ExaBGP communication)

### Docker Deployment
- Base image: `jirivrany/exafs-base` (Docker Hub)
- See `docs/DockerImage.md` for details
- Use Docker Compose for multi-container setup
- Reference: [ExaFS Ansible Deploy](https://github.com/CESNET/ExaFS-deploy)

## CI/CD Pipeline

### GitHub Actions
- **Workflow**: `.github/workflows/python-app.yml`
- **Triggers**: Push/PR to `master` or `develop` branches
- **Matrix**: Python 3.9, 3.10, 3.11, 3.12, 3.13
- **Steps**:
  1. Setup Python environment
  2. Set timezone (Europe/Prague)
  3. Install dependencies
  4. Run flake8 linting
  5. Run pytest test suite

### Running CI Locally
```bash
# Lint
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Test
pytest
```

## Git Workflow

### Branch Strategy
- `master` - Production releases
- `develop` - Development branch
- `claude/*` - AI assistant feature branches
- Feature branches for specific work

### Commit Messages
- Use descriptive commit messages
- Reference issue numbers: `fixes #74`
- Follow conventional commits when possible

### Version Releases
- Update version in `flowapp/__about__.py`
- Update `CHANGELOG.md`
- Create release tag
- Publish to PyPI

## Additional Resources

### Documentation Files
- `docs/INSTALL.md` - Detailed installation guide
- `docs/AUTH.md` - Authentication setup
- `docs/API.md` - API documentation reference
- `docs/DB_MIGRATIONS.md` - Database migration guide
- `docs/DB_BACKUP.md` - Database backup procedures
- `docs/DB_LOCAL.md` - Local database setup
- `docs/DockerImage.md` - Docker deployment
- `docs/guarda-service/` - Rule restoration service

### External Links
- [GitHub Repository](https://github.com/CESNET/exafs)
- [PyPI Package](https://pypi.org/project/exafs/)
- [Docker Hub](https://hub.docker.com/r/jirivrany/exafs-base)
- [ExaBGP](https://github.com/Exa-Networks/exabgp) - BGP engine
- [ExaBGP Process Package](https://pypi.org/project/exabgp-process/) - ExaBGP connector

### Related Projects
- **ExaFS Ansible Deploy**: Automated deployment with Ansible
- **ExaBGP Process**: Separate package for ExaBGP communication
- **Guarda Service**: Rule restoration monitor

## Quick Reference Commands

```bash
# Development
python run.py                          # Run development server
pytest                                 # Run tests
pytest -v                              # Verbose test output
pytest --cov=flowapp                   # Run with coverage
flask db migrate -m "message"          # Create migration
flask db upgrade                       # Apply migrations
flake8 .                              # Lint code

# Database
python db-init.py                      # Initialize database (runs migrations)
python db-init.py --reset              # Drop all tables and recreate (dev only)
flask db stamp 001_baseline            # Mark existing DB as baseline
flask db current                       # Show current migration
flask db history                       # Show migration history

# Production (via supervisord)
supervisorctl start exafs             # Start application
supervisorctl stop exafs              # Stop application
supervisorctl restart exafs           # Restart application
supervisorctl status                   # Check status
```

## Summary for AI Assistants

When working with this codebase:

1. **Always run tests** after making changes: `pytest`
2. **Create migrations** for model changes: `flask db migrate` — commit migration files to git
3. **Follow the service layer pattern** - business logic goes in services, not views
4. **Use existing validators** in `flowapp/validators.py` for validation
5. **Check authentication** - most routes need `@auth_required` decorator
6. **Respect rule limits** - use `check_rule_limit()` before creating rules
7. **Update Swagger docs** when adding API endpoints
8. **Follow existing patterns** - look at similar code for examples
9. **Test both web UI and API** when modifying rule functionality
10. **Consider ExaBGP output** - changes to rules may affect BGP command generation

The codebase is well-structured with clear separation of concerns. Follow the existing patterns and conventions for consistency.

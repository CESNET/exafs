# ExaFS Developer Guide

Detailed conventions and step-by-step task guides. Linked from `CLAUDE.md`.

## Common Development Tasks

### Adding a New Rule Field

1. **Update Model** (`flowapp/models/rules/*.py`)
   ```python
   new_field = db.Column(db.String(100), nullable=True)
   ```
2. **Create and apply migration**
   ```bash
   flask db migrate -m "Add new_field to Flowspec4"
   flask db upgrade
   ```
3. **Update Form** (`flowapp/forms/rules/*.py`)
   ```python
   new_field = StringField('New Field', validators=[Optional()])
   ```
4. **Update Service** (`flowapp/services/rule_service.py`) — add field handling in create/update
5. **Update Output** (`flowapp/output.py`) — include field in ExaBGP command if needed
6. **Add Tests** — test validation and full round-trip

### Adding a New API Endpoint

1. **Add Route** (`flowapp/views/api_v3.py`)
   ```python
   @api_v3.route('/endpoint', methods=['GET'])
   @jwt_required
   def new_endpoint():
       return jsonify(data), 200
   ```
2. **Update Swagger** (`flowapp/static/swagger.yml`)
3. **Add Tests** (`flowapp/tests/test_api_v3.py`)
   ```python
   def test_new_endpoint(auth_client):
       response = auth_client.get('/api/v3/endpoint')
       assert response.status_code == 200
   ```

### Adding a New Validator

1. **Create in** `flowapp/validators.py`
   ```python
   def validate_something(form, field):
       if not is_valid(field.data):
           raise ValidationError('Invalid value')
   ```
2. **Use in form field** validators list
3. **Add tests** in `flowapp/tests/test_validators.py`

## Code Conventions

### Python Style
- PEP 8, max line 127 chars, flake8 for linting
- Docstrings for complex functions

### Naming
- **Classes**: PascalCase (`Flowspec4`, `RuleService`)
- **Functions/Methods**: snake_case (`create_rule`, `validate_form`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_PORT`, `IPV4_PROTOCOL`)
- **Private**: leading underscore (`_validate_internal`)

### Imports
```python
# Standard library
import os
from datetime import datetime

# Third-party
from flask import Flask, render_template

# Local
from flowapp.models import User
from .validators import validate_ipv4
```

### Models
- Inherit from `db.Model`, set `__tablename__` explicitly
- Include `__repr__` for debugging
- Update `models/__init__.py` exports when adding new models

### Forms
- Inherit from `FlaskForm` or project base classes
- Business logic stays in services, not forms
- Form choices generated dynamically in `forms/choices.py`

### Views (Blueprints)
- One blueprint per functional area, keep views thin
- Use `@auth_required` on protected routes
- Status codes via return tuple: `return render_template(...), 404`
- JSON: `jsonify()`
- Don't query models directly — go through services

### Services
- Own all business logic
- Use DB transactions appropriately
- Raise descriptive exceptions, log important operations
- Don't import from views — services are independent

## Testing Conventions

### Structure (AAA pattern)
```python
def test_feature_name(client):
    # Arrange
    # Act
    response = client.get('/endpoint')
    # Assert
    assert response.status_code == 200
```

### Fixtures
- `client` — unauthenticated Flask test client
- `auth_client` — authenticated test client
- `app` — Flask application instance
- DB is reset between tests

### File Naming
- Prefix `test_`: `test_models.py`, `test_api_v3.py`
- Test both success and failure cases

## Security Checklist

- Never bypass `@auth_required`
- Call `check_user_can_modify_rule()` before any rule modification
- Call `check_rule_limit()` / `check_global_rule_limit()` before creating rules
- Use WTForms validators + server-side BGP syntax validation
- Use SQLAlchemy ORM — never raw SQL with user input
- CSRF tokens in all templates; exempt API endpoints explicitly
- Secrets in config/env, never hardcoded

## Deployment Notes

- **Web server**: Apache + mod_proxy_uwsgi
- **WSGI**: uWSGI, **Process manager**: Supervisord
- **Auth (prod)**: Shibboleth SSO
- **ExaBGP comms**: RabbitMQ (preferred) or HTTP
- **Docker base image**: `jirivrany/exafs-base`; see `docs/DockerImage.md`
- **Ansible deploy**: [ExaFS-deploy](https://github.com/CESNET/ExaFS-deploy)
- Production: `DEBUG = False`, strong `SECRET_KEY` and `JWT_SECRET`, HTTPS

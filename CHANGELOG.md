# Changelog

All notable changes to ExaFS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.2] - 2026-02-16

### Changed
- **Database migrations now tracked in git** — `migrations/` removed from `.gitignore`
- Replaced `db-init.py` with migration-based initialization (`flask db upgrade`)
- Removed one-time `/admin/set-org-if-zero` endpoint, replaced with standalone `scripts/migrate_v0x_to_v1.py`
- Fixed Flask-SQLAlchemy deprecation warning in Alembic `env.py`
- Template URLs changed to use `url_for` helper, removed unused `rule.html` template

### Added
- Idempotent baseline migration (`001_baseline`) that brings any ExaFS database (from v0.4+ to current) to the v1.2.2 schema
- Optional `scripts/migrate_v0x_to_v1.py` helper for v0.x to v1.0+ data migration (org_id backfill)
- `db-init.py --reset` flag for development database reset
- `PYTHONPATH` set in Docker dev container for easier development

## [1.2.1] - 2026-01-30

### Fixed
- Fixed nested `<form>` elements in dashboard tables causing delete button to fail on the first row
- Delete actions reverted from POST forms to GET links with CSRF token passed as URL query parameter
- CSRF protection preserved via manual `validate_csrf` check in delete endpoints

## [1.2.0] - 2026-01-29

### Security
- Changed delete operations from GET to POST requests to prevent CSRF attacks
- Fixed possible wrong behavior of `admin_or_user_required` auth decorator
- Fixed wrong session key in `rules.py` `is_admin` function

### Added
- GRE protocol support
- AS Paths added to admin menu

### Changed
- Tests moved outside `flowapp` package
- Updated documentation schema

## [1.1.9] - 2025-11-18

### Fixed
- bugfix for #74 new RTBH records can be created in wrong state

## [1.1.8] - 2025-10-20

### Fixed
- check all for group edit / delete

### Added 
- pagination for Expired and All Dashboard cards
- search form quick clear by button or ESC key
- improved search to work with paginated data

## [1.1.7] - 2025-10-16

### Fixed
- Fixed config loading to use Flask instance folder
- Resolves path issues when package is installed via pip

## [1.1.6] - 2025-10-08

### Fixed
- Fixed problem with session overflow on too many rules id

### Changed
- Updated `withdraw_expired` method to also delete expired rules
- Expiration threshold can now be set in config (default: 30 days)

### Added
- New auth helpers to determine which rules a user can modify
- Functions `get_user_allowed_rule_ids` and `check_user_can_modify_rule` in auth module
- `EXPIRATION_THRESHOLD` config option
- PyPi package published
- Docker base image published
- updated docs

## [1.1.5] - 2025-10-06

### Added
- Introduced instance config override
- Copy the sample to `instance_config_override.py` to customize dashboard menu items easily

### Changed
- For normal installations, no override is needed
- Changed `MAX_COMMA_VALUES` constant to 5 as default value

## [1.1.4] - 2025-08-20

### Fixed
- Minor bug fixes
- More robust function for filtering and splitting flowspec rules for user

### Changed
- Code cleanup
- Updated filter rules action to be more robust

## [1.1.3] - 2025-07-14

### Added
- Introduced configurable footer menu for links in bottom of the default template

### Changed
- Removed debug print statements in update_set_org

## [1.1.2] - 2025-07-02

### Security
- Minor security updates (removed unused JS files)

### Changed
- `setup.py` now reads dependencies from `requirements.txt`

### Fixed
- Fixed bugs for flowspec limit in various views

## [1.1.1] - 2025-06-03

### Changed
- **Machine API Key rewritten**
  - API keys for machines are now tied to one of the existing users
  - If there is a need to have API access for machine, first create service user and set the access rights
  - Then create machine key as Admin and assign it to this user
  - Machine key now has user rights of the assigned user, not of admin

## [1.1.0] - 2025-03-25

### Added
- **RTBH Whitelist Integration**
  - System automatically evaluates new RTBH rules against existing whitelists
  - Can automatically modify or block rules that conflict with whitelisted networks
  - Automatically whitelist rules that exactly match or are contained within whitelisted networks
  - Create subnet rules when RTBH rules are supersets of whitelisted networks
  - Maintain rule cache that tracks relationships between rules and whitelists for proper cleanup
- Dedicated services layer for better separation of concerns
  - `rule_service.py` for rule management operations
  - `whitelist_service.py` for whitelist functionality
  - `whitelist_common.py` for shared whitelist utilities

### Changed
- **Major Architecture Refactoring**
  - Significant architectural refactoring focused on better separation of concerns
  - Improved maintainability through services layer
  - Business logic extracted from view controllers
- **Models structure reorganization**
  - Better separation into logical modules
  - Rule models organized under `flowapp/models/rules/`
  - Separate files for different rule types (`flowspec.py`, `rtbh.py`, `whitelist.py`)
  - Backward compatibility maintained through main models `__init__.py`
- **Form handling improvements**
  - Better organization under `flowapp/forms/`
  - Enhanced validation logic

## [1.0.2] - 2025-03-19

### Fixed
- Fixed bug in IPv6 Flowspec messages
- Fixed JSON output for route if ExaBGP process HTTP API is used
- Empty fragment in IPv6 messages should be empty string not None

## [1.0.1] - 2025-01-09

### Fixed
- Minor bug fixes

### Changed
- Application is now Flask 3 compliant (updated requirements)

## [1.0.0] - 2024-10-15

### Added
- Limits for number of rules in the system
  - Limits for rules per organization
  - Overall limit for the installation
- Rules are now tied to organization
  - Organization selection required after login for users belonging to multiple organizations
- Bulk import for users enabled for admin
- Swagger documentation for API on local system (available at `/apidocs` URL)
- New format of message for ExaAPI
  - Now sends information about rule author (user) for logging purposes

### Changed
- **Database schema changes** - migration required
  - Existing rules need to be linked to organizations
  - See [detailed migration documentation](./docs/DB_MIGRATIONS.md)
- ExaAPI and Guarda modules moved outside of the project
  - ExaAPI now available as [pip package exabgp-process](https://pypi.org/project/exabgp-process/)
  - ExaAPI has own [GitHub repository](https://github.com/CESNET/exabgp-process)
- Watch of ExaBGP restart can be done by guarda service or by override of the ExaBGP service settings

## [0.8.1] - 2024-09-23

### Changed
- Application now uses Flask-Session stored in DB using SQL Alchemy driver
- Can be configured for other drivers
- Server-side session is required for proper application function

## [0.8.0] - 2024-03-28

### Added
- API keys expiration date
- API keys readonly flag
- Admin can create special keys for certain machines

### Changed
- **API keys update** - migration required
- Run migration scripts to update your database

## [0.7.3] - 2023-11-03

### Added
- New possibility of external auth proxy
- Support for authentication using external proxy (expects HTTP header authentication)

## [0.7.2] - 2023-07-12

### Added
- Dashboard and Main menu are now customizable in config

### Changed
- App is ready to be packaged using `setup.py`

## [0.7.0] - 2022-09-02

### Added
- ExaAPI now has two options: HTTP or RabbitMQ

### Changed
- ExaAPI process has been renamed
- Update of ExaBGP process value is needed for this version

## [0.6.2] - 2022-09-02

### Added
- External config for ExaAPI

## [0.6.0] - 2022-04-29

### Changed
- Bootstrap 5 in UI

## [0.5.5] - 2022-02-25

### Changed
- API v3: auth API key in cookie, not in URL

## [0.5.4] - 2021-08-31

### Added
- Right click menu on address with Whois or Copy to clipboard functionality

### Fixed
- Fixed `form.process()` bug

## [0.5.3] - 2021-06-30

### Changed
- Dashboard update
- Forms with default action (no default action/community in forms)

## [0.5.2] - 2021-04-16

### Changed
- API v2 with new keys

## [0.5.1] - 2021-03-27

### Fixed
- Bug fixes

### Added
- Urgent and push values for TCP FLAGS

## [0.5.0] - 2021-03-09

### Changed
- **New format of LOG table in database** - migration required
- Run migration scripts to update your database
- Removed foreign key `user_id`
- Author email is stored directly to logs for faster grep text search

## [0.4.8] - 2020

### Added
- Enhanced String Filtering

## [0.4.7] - 2020

### Added
- Multi neighbor support enabled
- See config example and update your `config.py`

## [0.4.6] - 2020

### Added
- Route Distinguisher for VRF now supported
- See config example and update your `config.py`

[1.2.2]: https://github.com/CESNET/exafs/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/CESNET/exafs/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/CESNET/exafs/compare/v1.1.9...v1.2.0
[1.1.9]: https://github.com/CESNET/exafs/compare/v1.1.8...v1.1.9
[1.1.8]: https://github.com/CESNET/exafs/compare/v1.1.7...v1.1.8
[1.1.7]: https://github.com/CESNET/exafs/compare/v1.1.6...v1.1.7
[1.1.6]: https://github.com/CESNET/exafs/compare/v1.1.5...v1.1.6
[1.1.5]: https://github.com/CESNET/exafs/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/CESNET/exafs/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/CESNET/exafs/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/CESNET/exafs/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/CESNET/exafs/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/CESNET/exafs/compare/v1.0.2...v1.1.0
[1.0.2]: https://github.com/CESNET/exafs/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/CESNET/exafs/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/CESNET/exafs/compare/v0.8.1...v1.0.0
[0.8.1]: https://github.com/CESNET/exafs/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/CESNET/exafs/compare/v0.7.3...v0.8.0
[0.7.3]: https://github.com/CESNET/exafs/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/CESNET/exafs/compare/v0.7.0...v0.7.2
[0.7.0]: https://github.com/CESNET/exafs/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/CESNET/exafs/compare/v0.6.0...v0.6.2
[0.6.0]: https://github.com/CESNET/exafs/compare/v0.5.5...v0.6.0
[0.5.5]: https://github.com/CESNET/exafs/compare/v0.5.4...v0.5.5
[0.5.4]: https://github.com/CESNET/exafs/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/CESNET/exafs/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/CESNET/exafs/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/CESNET/exafs/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/CESNET/exafs/compare/v0.4.8...v0.5.0
[0.4.8]: https://github.com/CESNET/exafs/compare/v0.4.7...v0.4.8
[0.4.7]: https://github.com/CESNET/exafs/compare/v0.4.6...v0.4.7
[0.4.6]: https://github.com/CESNET/exafs/releases/tag/v0.4.6


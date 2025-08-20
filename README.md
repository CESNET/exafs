# ExaFS
ExaFS brings new functionality to the environment of routing protocols configuration for backbone network hardware security. 

The tool extends network administrators toolset by adding an extra layer for configuration rules creation, validation, and authorization. With this new layer, a larger group of network administrators can safely create new
 [BGP protocol](https://github.com/Exa-Networks/exabgp) rules to prevent DDoS and other forms of malicious cyber attacks. 

ExaFS is open source with MIT license. The system is regularly used at [CESNET](https://www.cesnet.cz/) - the Czech national e-infrastructure for science, research and education operator.

ExaFS provides both the user Web interface and the REST API for web service. 

Key contributions of the system are **user authorization** mechanism and **validation system for BGP commands**.

Without ExaFS the system Root privileges are required for direct interaction with ExaBGP and networking hardware. ExaFS provides several user roles and access rights similarly to user roles in other software systems such as SQL. The system allows specifying user rights for various kinds of sub-nets following the network topology.

Validation system for BGP commands assures that only error-free messages can pass to the system BGP API. Both syntax and access rights are validated before a new rule can be stored in the database.

Thanks to the storage, all the rules can be restored quickly after a system reboot or failure. All rules are validated again, before sending them to ExaBPG from the storage, to prevent any malicious database manipulation.

ExaFS is an integral part of cybersecurity tools at CESNET. However, it can be used in any network where ExaBGP is available.

See how is ExaFS integrated into the network in the picture below. 


![ExaFS integration schema](./docs/schema.png)

## Project presentations

* 2020 - CZ [DDoS Protector v prostředí propojovacího uzlu NIX.CZ](https://www.cesnet.cz/wp-content/uploads/2020/02/DDP_v_NIX.pdf), [Seminář o bezpečností sítí a služeb 2020](https://www.cesnet.cz/akce/bss20/)
* 2019 - EN [ExaFS: mitigating unwanted traffic](https://xn--ondej-kcb.caletka.cz/dl/slidy/20191113-SIGNOC-ExaFS.pdf), [10th SIG-NOC meeting](https://wiki.geant.org/display/SIGNOC/10th+SIG-NOC+meeting), Prague
* 2019 - CZ [Potlačení nežádoucího provozu pomocí BGP Flowspec](https://indico.csnog.eu/event/6/contributions/64/attachments/35/61/CESNET-FlowSpec-CSNOG.pdf), [CSNOG 2019](https://indico.csnog.eu/event/6/overview) 
* 2019 - CZ [Nástroje pro FlowSpec a RTBH](https://konference.cesnet.cz/prezentace2019/sal1/3_Adamec.pdf), [Konference e-infrastruktury CESNET](https://konference.cesnet.cz/) 2019
* 2019 - CZ [Nástroje pro obranu proti útokům na páteřních směrovačích](https://konference.cesnet.cz/prezentace2019/sal1/3_Verich.pdf),[Konference e-infrastruktury CESNET](https://konference.cesnet.cz/) 2019


## System overview

![ExaFS schema](./docs/app_schema_en.png)
The core component of ExaFS is a web application written in Python using the Flask framework. It provides a user interface for managing ExaBGP rules (CRUD operations) and also exposes a REST API with similar functionality. The web application uses Shibboleth for authentication, while the REST API relies on token-based authentication.

The application generates ExaBGP commands and forwards them to the ExaBGP process. All rules are thoroughly validated—only valid rules are stored in the database and sent to the ExaBGP connector.

The second component of the system is a separate application that replicates received commands to `stdout`. The connection between the ExaBGP daemon and the `stdout` of the ExaAPI (ExaBGP process) is defined in the ExaBGP configuration.

This API was originally part of the same project but has since been moved to its own repository. You can use the [exabgp-process pip package](https://pypi.org/project/exabgp-process/), clone the Git repository, or develop your own implementation.

Each time this process receives a command from ExaFS, it outputs it to `stdout`, allowing the ExaBGP service to process the command and update its routing table—creating, modifying, or removing rules accordingly.

It may also be necessary to monitor ExaBGP and re-announce rules after a restart or shutdown. This can be handled via the ExaBGP service configuration, or by using an example system service called **Guarda**, described in the documentation. In either case, the key mechanism is calling the application endpoint `/rules/announce_all`. This endpoint is only accessible from `localhost`; a local IP address must be configured in the application settings.

## DOCS
### Instalation related
* [ExaFS Ansible deploy](https://github.com/CESNET/ExaFS-deploy) - repository with Ansbile playbook for deploying ExaFS with Docker Compose. 
* [Install notes](./docs/INSTALL.md)
* [Database backup configuration](./docs/DB_BACKUP.md)
* [Local database instalation notes](./docs/DB_LOCAL.md)
### API
The REST API is documented using Swagger (OpenAPI). After installing and running the application, the API documentation is available locally at the /apidocs/ endpoint. This interactive documentation provides details about all available endpoints, request and response formats, and supported operations, making it easier to integrate and test the API.



## Change Log
- 1.1.4 - minor bug fixes and code cleanup
- 1.1.3 - introduced configurable footer menu for links in bottom of the default template
- 1.1.2 - minor security updates (removed unused JS files), setup.py now reads dependencies from requirements.txt
- 1.1.1 - Machine API Key rewrited. 
    - API keys for machines are now tied to one of the existing users. If there is a need to have API access for machine, first create service user, and set the access rights. Then create machine key as Admin and assign it to this user. 
- 1.1.0 - Major Architecture Refactoring and Whitelist Integration
    - Code Organization and Architecture Improvements. Significant architectural refactoring focused on better separation of concerns and improved maintainability. The most notable change is the introduction of a dedicated **services layer** that extracts business logic from view controllers. Key service modules include `rule_service.py` for rule management operations, `whitelist_service.py` for whitelist functionality, and `whitelist_common.py` for shared whitelist utilities. 
    - The **models structure** has been reorganized with better separation into logical modules. Rule models are now organized under `flowapp/models/rules/` with separate files for different rule types (`flowspec.py`, `rtbh.py`, `whitelist.py`), while maintaining backward compatibility through the main models `__init__.py`. Form handling has also been improved with better organization under `flowapp/forms/` and enhanced validation logic.
    - **RTBH Whitelist Integration** This system automatically evaluates new RTBH rules against existing whitelists and can automatically modify or block rules that conflict with whitelisted networks. When an RTBH rule is created that intersects with a whitelist entry, the system can:
        - **Automatically whitelist** rules that exactly match or are contained within whitelisted networks
        - **Create subnet rules** when RTBH rules are supersets of whitelisted networks, automatically generating the non-whitelisted portions
        - **Maintain rule cache** that tracks relationships between rules and whitelists for proper cleanup
- 1.0.2 - fixed bug in IPv6 Flowspec messages
- 1.0.1 . minor bug fixes
- 1.0.0 . Major changes
    - Limits for nuber of rules in the system introduced. There are now limits for rules for organization and overall limit for the instalation. Database changed / migration is required. Migrating the database to version 1.0.x is a bit more complicated, you need to link existing rules to organizations. [A more detailed description is in a separate document](./docs/DB_MIGRATIONS.md).
    - Rules are now tied to organization. If the user belongs to more than one organization, the organization for the session must be selected after login.
    - Bulk import for users enabled for admin.
    - Introduced Swagger docs for API on the local system. Just open /apidocs url. 
    - New format of message for ExaAPI - now sends information about author of rule (user) for logging purposes.
    - ExaAPI and Guarda modules moved outside of the project.
    - ExaAPI is now available as a [pip package exabgp-process](https://pypi.org/project/exabgp-process/), with own [github repostiory](https://github.com/CESNET/exabgp-process).
    - Watch of exabgp restart can be still done by guarda service - see docs. Or it can be done by override of the exabgp service settings.  
- 0.8.1 application is using Flask-Session stored in DB using SQL Alchemy driver. This can be configured for other drivers, however server side session is required for the application proper function.
- 0.8.0 - API keys update.  **Run migration scripts to update your DB**.  Keys can now have expiration date and readonly flag. Admin can create special keys for certain machinnes.
- 0.7.3 - New possibility of external auth proxy. 
- 0.7.2 - Dashboard and Main menu are now customizable in config. App is ready to be packaged using setup.py.
- 0.7.0 - ExaAPI now have two options - HTTP or RabbitMQ. ExaAPI process has been renamed, update of ExaBGP process value is needed for this version.
- 0.6.2 - External config for ExaAPI 
- 0.6.0 - Bootstrap 5 in UI
- 0.5.5 - API v3 - auth api key in cookie not in url
- 0.5.4 - Right click menu on adress / Whois or Copy to clipboard
- 0.5.3 - Dashboard update, forms with default action
- 0.5.2 - API v2 with new keys 
- 0.5.1 - Bug fixes
- 0.5.0 - New format of LOG table in database. **Run migration scripts to update your DB**. Removed foreign key user_id, author email is stored directly to logs for faster grep text search.
- 0.4.8 - Enhanced String Filtering
- 0.4.7 - Multi neighbor support enabled. See config example and update your config.py. 
- 0.4.6 - Route Distinguisher for VRF is now supported. See config example and update your config.py. 

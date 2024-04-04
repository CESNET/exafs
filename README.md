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

The central part of the ExaFS is a web application, written in Python3.6 with Flask framework. It provides a user interface for ExaBGP rule CRUD operations. The application also provides the REST API with CRUD operations for the configuration rules. The web app uses Shibboleth authorization; the REST API is using token-based authorization. 

The app creates the ExaBGP commands and forwards them to ExaAPI. All rules are carefully validated, and only valid rules are stored in the database and sent to the ExaBGP connector.
 
This second part of the system is another web application that replicates the received command to the stdout. The connection between ExaBGP daemon and stdout of ExaAPI is specified in the ExaBGP config. 
 
Every time this API gets a command from ExaFS, it replicates this command to the ExaBGP daemon through the stdout. The registered daemon then updates the ExaBGP table – create, modify or remove the rule from command.
Last part of the system is Guarda service. This systemctl service is running in the host system and gets a notification on each restart of ExaBGP service via systemctl WantedBy config option. For every restart of ExaBGP the Guarda service will put all the valid and active rules to the ExaBGP rules table again.

## DOCS
* [Install notes](./docs/INSTALL.md)
* [API documentation ](https://exafs.docs.apiary.io/#)
* [Database backup configuration](./docs/DB_BACKUP.md)
* [Local database instalation notes](./docs/DB_LOCAL.md)

## Change Log
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

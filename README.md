# Exafs tool

ExaFS is a web application for creation, validation, and execution of ExaBGP messages (https://github.com/Exa-Networks/exabgp).

It provides two main interfaces – the User web interface and the REST API.  The system provides user authentication mechanism, access control system and message validation system. 

The toolset was created and tested at CESNET but it can be used in any network where ExaBGP is available.

On the picture below you can see as the ExaFS is integrated into the network.

![ExaFS schema](./docs/schema.png)

## Main parts

The main part of the ExaFS is a web application, written in Python - Flask. It provides a user interface for ExaBGP rule adding editing and deleting. All rules are carefully validated and only valid rules are sent to the ExaBGP table.  This application also provides the REST API with CRUD operations for the configuration rules.

The web app creates the ExaBGP commands and forwards them to ExaAPI. This second part of the system is a very simple web application that replicates the received command to the stdout. The ExaBGP daemon must be configured for monitoring stdout of ExaAPI. Every time this API gets a  command from ExaFS,  it replicates this command to the ExaBGP daemon through the stdout. The registered daemon then updates the ExaBGP table – create, modify or remove the rule from command.

Last part of the system is Guarda service. This systemctl service is running in the host system and is wanted by ExaBGP service.  That means for every restart of ExaBPG this service will start and again put the valid and active rules to Exa table. 
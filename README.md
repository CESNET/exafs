# Exafs tool

Exafs is a tool for creation, validation, and execution 
of [ExaBGP messages](https://github.com/Exa-Networks/exabgp).
It provides two interfaces - the Web app and the REST API. Both combined with user authentication mechanism, access control system and message validation system. 

The toolset was created and tested at CESNET by Jiri Vrany, Petr Adamec, and Josef Verich. 

## Main parts

We assume that you are have working ExaBGP system and looking for a tool for administration.

The main part of the ExaFS is **web application**, written in Python - Flask. It provides a user interface for ExaBGP rule
adding editing and deleting. All rules are carefully validated and only valid rules are sent to the
ExaBGP table. 

The web app sends the ExaBGP commands to ExaAPI. This is a very simple
web application, which needs to be hooked on ExaBGP daemon. Every time this app
gets a new command, it replicates the command to the daemon through the stdout. The registered daemon is watching the stdout of the ExaAPI service.

Last part of the system is Guarda service. This service is running in the system and is wanted by ExaBGP. That means for every restart of ExaBPG this service will again put the valid and active rules
to Exa table. 
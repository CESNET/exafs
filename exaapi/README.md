#ExaAPI web app 

This is a very simple web application, which needs to be hooked on ExaBGP daemon. Every time this app
gets a new command, it replicates the command to the daemon through the stdout. The registered
daemon is watching the stdout of the ExaAPI service.

Add this to your ExaBGP config
```
process flowspec {
         run /usr/bin/python3 /home/deploy/www/exaapi/exa_api.py;
         encoder json;
    }
```

It can run on the development Flask server, however there is no security layer in this app. 
You should limit the access only from the localhost. 

Our plan is to relace this simple app with message queue in the future.


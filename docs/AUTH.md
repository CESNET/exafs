# ExaFS tool
## Auth mechanism

Since version 0.7.3, the application supports three different forms of user authorization. 

* SSO using Shibboleth
* Simple Auth proxy 
* Local single-user mode 

### SSO
To use SSO, you need to set up Apache + Shiboleth in the usual way. Then set `SSO_AUTH = True` in the application configuration file **config.py**

Shibboleth configuration example:

#### shibboleth config:
```
<Location />
  AuthType shibboleth
  ShibRequestSetting requireSession 1
  require shib-session
</Location>

```


#### httpd ssl.conf 
We recomend using app with https only. It's important to configure proxy pass to uwsgi in httpd config.
```
# Proxy everything to the WSGI server except /Shibboleth.sso and
# /shibboleth-sp
ProxyPass /kon.php !
ProxyPass /Shibboleth.sso !
ProxyPass /shibboleth-sp !
ProxyPass / uwsgi://127.0.0.1:8000/
```

### Simple Auth
This mode uses a WWW server (usually Apache) as an auth proxy. It is thus possible to use an external user database. Everything needs to be set in the web server configuration, then in **config.py** enable `HEADER_AUTH = True` and set `AUTH_HEADER_NAME = 'X-Authenticated-User'` 

See [apache.conf.example]('./apache.example.conf') for more information about configuration.

### Local single user mode
This mode is used as a fallback if neither SSO nor Simple Auth is enabled. Configuration is done using **config.py**. The mode is more for testing purposes, it does not allow to set up multiple users with different permission levels and also does not perform user authentication. 
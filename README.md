# Flowspec tool

## Production confg/install

### shibboleth config:
```
<Location /login>
  AuthType shibboleth
  ShibRequestSetting requireSession 1
  require shib-session
</Location>

```

### httpd ssl.conf

```
# Proxy everything to the WSGI server except /Shibboleth.sso and
# /shibboleth-sp
ProxyPass /kon.php !
ProxyPass /Shibboleth.sso !
ProxyPass /shibboleth-sp !
ProxyPass / uwsgi://127.0.0.1:8000/
```

### Flask app

* as root run:  yum install -y python-devel gcc




## Devel config

### Run Mariadb in docker

'''
docker run --name=flowspec-db --env="MYSQL_ROOT_PASSWORD=my-secret-pw"  --volume="/home/albert/work/flowspec/datadir:/var/lib/mysql" -p 3306:3306 --restart=no mariadb:5.5 
'''
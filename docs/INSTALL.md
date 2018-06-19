# ExaFS tool
## Production install and config notes

Example of full instalation and deployment in production enviroment. 
Includes: shibboleth auth, mariadb, uwsgi, supervisord


### shibboleth config:
```
<Location /login>
  AuthType shibboleth
  ShibRequestSetting requireSession 1
  require shib-session
</Location>

```

### httpd ssl.conf with shibboleth

```
# Proxy everything to the WSGI server except /Shibboleth.sso and
# /shibboleth-sp
ProxyPass /kon.php !
ProxyPass /Shibboleth.sso !
ProxyPass /shibboleth-sp !
ProxyPass / uwsgi://127.0.0.1:8000/
```

### Flask app

#### Install python runtime and other deps 
As root. Install dependencies. If you are using Debian or Ubunutu, you must of course use apt and sudo instead yum.
```
yum install -y python-devel gcc
yum install mod_proxy_uwsgi   
yum install mariadb mariadb-server mariadb-devel
```
Start db and secure instalation
```
systemctl start mariadb
mysql_secure_installation
systemctl enable mariadb
```
Install python dependencies
```
pip install virtualenv honcho uwsgi
```

#### Prepare the db

Now prepare the database. Start mysql client with
```
mysql -u root -p 
```
Now create the db and user
```
create database exafs;
CREATE USER 'exafs'@'localhost' IDENTIFIED BY 'password'; insert some real password
use exafs;
GRANT ALL PRIVILEGES ON exafs.* TO 'exafs'@'localhost';
FLUSH PRIVILEGES;
exit;
```

#### App instalation
As deploy user pull the source codes, create virtualenv and install required python dependencies.
```
clone source from repository: git clone git@github.com:CESNET/exafs.git www
cd www
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### make selinux happy - As root
```
setsebool httpd_can_network_connect 1
``` 

#### Supervisord - install as root
1. install:
   `pip install supervisor`
2. configure:
   1. `mkdir -p /etc/supervisord/conf.d`
   2. `echo_supervisord_conf > /etc/supervisord/supervisord.conf`
   3. `echo "[include]" >> /etc/supervisord/supervisord.conf`
   4. `echo "files = conf.d/*.conf" >> /etc/supervisord/supervisord.conf`
   
   
3. setup as service:
   `wget supervisord.service -O /usr/lib/systemd/system/supervisord.service`
4. start service
   `systemctl start supervisord`
5. view service status:
   `systemctl status supervisord`
6. auto start service on system startup: 
   `systemctl enable supervisord`
7. copy exafs.supervisord.conf to /etc/supervisord/
  `cp exafs.supervisord.conf /etc/supervisord/conf.d/`

#### Final steps - as deploy user
Create and populate database tables.
```
cd ~/www
source venv/bin/activate
python db-init.py
```

#### As root
Prepare the log dir, start services.
```
mkdir /var/log/flowspec/
systemctl start httpd
systemctl start supervisord
```

You are ready to go ;-)
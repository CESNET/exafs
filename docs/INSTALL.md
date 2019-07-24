# ExaFS tool
## Production install and config notes

Example of ExaFS instalation and deployment in production enviroment. 
Includes: shibboleth auth, mariadb, uwsgi, supervisord

## Prerequisites

ExaFS is using shibboleth auth and therefore we suggest to use Apache web server. 
Install the Apache httpd as usual and then continue with this guide.  


### shibboleth config:
```
<Location />
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
As root. Install dependencies. If you are using Debian or Ubuntu, you must of course use apt and sudo instead yum.
```
yum install python-devel gcc
yum install mod_proxy_uwsgi uwsgi-plugin-python2 
yum install mariadb mariadb-server mariadb-devel
```
Start db and secure instalation
```
systemctl start mariadb
mysql_secure_installation
systemctl enable mariadb
```
Install VirtualEnv for Python
```
pip install virtualenv
```

#### Prepare the db

Now prepare user for the database. Start mysql client with
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

#### As root
Prepare the log dir, start httpd if not already running.
```
mkdir /var/log/flowspec/
systemctl start httpd
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
    1. download supervisord.service file from [this gist](https://gist.github.com/mozillazg/6cbdcccbf46fe96a4edd)
    2. `wget supervisord.service -O /usr/lib/systemd/system/supervisord.service`
4. start service
   `systemctl start supervisord`
5. view service status:
   `systemctl status supervisord`
6. auto start service on system startup: 
   `systemctl enable supervisord`
7. copy exafs.supervisord.conf to /etc/supervisord/
  `cp exafs.supervisord.conf /etc/supervisord/conf.d/`

#### Final steps - as deploy user

Copy config.example.py to config.py and fill out the DB credetials. 

Create and populate database tables.
```
cd ~/www
source venv/bin/activate
python db-init.py
```
DB-init script inserts default roles, actions, rule states and two organizations (TUL and Cesnet). But no users.

So before start, use your favorite mysql admin tool and insert some users into database. 
The uuid of user should be set the eppn value provided by Shibboleth. 

You can use following MYSQL commands to insert the user, give him role 'admin' and add him to the the organization 'Cesnet'.

```
insert into user (uuid,email,name) values ('example@cesnet.cz', 'example@cesnet.cz', 'Mr. Example Admin');
insert into user_role (user_id,role_id) values (1, 3);
insert into user_role (user_id,organization_id) values (1, 2);
``` 
You can also modify the models.py for your own default values for db-init.


You are ready to go ;-)
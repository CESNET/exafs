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

#### As root
* yum install -y python-devel gcc
* yum install mod_proxy_uwsgi   
* yum install mariadb mariadb-server mariadb-devel
* systemctl start mariadb
* mysql_secure_installation
* systemctl enable mariadb
* pip install virtualenv honcho uwsgi
* mysql -p

#### As mysql root
* create database flowspec;
* CREATE USER 'flowspec'@'localhost' IDENTIFIED BY 'password'; insert some real password
* use flowspec;
* GRANT ALL PRIVILEGES ON flowspec.* TO 'flowspec'@'localhost';
* FLUSH PRIVILEGES;
* exit;

#### As deploy user

* clone source from repository: git clone git@homeproj.cesnet.cz:flowspec www
* cd www
* virtualenv venv
* source venv/bin/activate
* pip install -r requirements.txt

#### As root
* make selinux happy: setsebool httpd_can_network_connect 1 
* pip install supervisor

#### Supervisor as root
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
7. copy flowspec.conf to supervisord.conf

#### As deploy user

* cd ~/www
* source venv/bin/activate
* honcho export -a myapp supervisord /etc/supervisor/conf.d
* v /etc/supervisor/conf.d change user to deploy


#### As root
* mkdir /var/log/flowspec/
* systemctl restart httpd
* systemctl restart supervisord

## MariaDB backup

### as Mysql root
* GRANT LOCK TABLES, SELECT, SHOW VIEW, REPLICATION CLIENT ON *.* TO 'db_user_backups'@'%' IDENTIFIED BY 'password';
* to make sure MySQL is configured to properly restore stored procedures > SET GLOBAL log_bin_trust_function_creators = 1;

### as root
* mkdir /backups && cd /backups
* touch .env db-backup.sh db-backup.log
* chmod -R 775 /backups
* chmod +x db-backup.sh

#### add mysql backup user credentials into environment file
* echo "export MYSQL_USER=db_user_backups" >> /backups/.env
* echo "export MYSQL_PASS={COMPLEX-PASSWORD}" >> /backups/.env

#### Backup script
```
#!/bin/bash

BKUP_DIR="/backups"
BKUP_NAME="`date +%Y%m%d%H%M`-backup-flowspec.sql.gz"

# get backup users credentials
source $BKUP_DIR/.env

# create backups
# NOTE: --routines flag makes sure stored procedures are also backed up
mysqldump --routines flowspec -u ${MYSQL_USER} -p${MYSQL_PASS} | gzip > ${BKUP_DIR}/${BKUP_NAME}

```



## Emergency start as deploy user
* cd ~/www
* source venv/bin/activate
* honcho start &


## Devel config

### Run Mariadb in docker

'''
docker run --name=flowspec-db --env="MYSQL_ROOT_PASSWORD=my-secret-pw"  --volume="/home/albert/work/flowspec/datadir:/var/lib/mysql" -p 3306:3306 --restart=no mariadb:5.5 
'''

### @TODO

- neexistující uživatel vyvolá 500 - potřeba ošetřit 
- doinstalovat guarda / service pro restart serveru
# ExaFS tool
## Production install and config notes

Example of ExaFS installation od RHEL/Centos 9 and deployment in production enviroment. 
Includes: shibboleth auth, mariadb, uwsgi, supervisord

The default Python for RHEL9 is Python 3.9
Virtualenv with Python39 is used by uWSGI server to keep the packages for app separated from system.

## Prerequisites
First, choose how to [authenticate and authorize users](./AUTH.md). The application currently supports three options. 

Depending on the selected WWW server, set up a proxy. We recommend using Apache + mod_uwsgi. If you use another solution, set up the WWW server as you are used to. 

```
# Proxy everything to the WSGI server
ProxyPass / uwsgi://127.0.0.1:8000/
```

### Main app
The ExaFS is using Flask Python Framework. We are using standard deployment for Flask and Apache
as is described in the offical docs. 

#### Install python runtime and other dependencies 
Install dependencies as root. 

If you are using Debian or Ubuntu, you must of course use apt and sudo instead yum. 

Don't forget to enable mod_proxy_uwsgi module in your Apache httpd config. 
MariaDB is not a strict requirement, the app is using SQL-Alchemy and therefore you can use another RDBMS if needed.

Install Python, UWSGI and MariaDB.
```
yum install gcc python3 python3-devel
yum install mod_proxy_uwsgi uwsgi-plugin-python3
yum install mariadb mariadb-server mariadb-devel
```

Start MariaDB and secure instalation
```
systemctl start mariadb
mysql_secure_installation
systemctl enable mariadb
```

Next step is to install VirtualEnv for Python
```
pip install virtualenv
```

#### Setup the database connection

Now prepare user for the database. Start mysql client with
```
mysql -u root -p 
```
Now create the db and user with password
```
CREATE DATABASE exafs;
ALTER DATABASE exafs CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE USER 'exafs'@'localhost' IDENTIFIED BY 'verysecurepassword'; 

USE exafs;
GRANT ALL PRIVILEGES ON exafs.* TO 'exafs'@'localhost';
FLUSH PRIVILEGES;
exit;
```

#### App instalation
Create new user called **deploy** in the system.

As deploy user pull the source codes from GH, create virtualenv and install required python dependencies.
```
su - deploy
clone source from repository: git clone https://github.com/CESNET/exafs.git www
cd www
virtualenv --python=python3.9 venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Next steps (as root)

Now lets continue as root user once again. 

First we need to allow httpd connection in SeLinux

```
setsebool -P httpd_can_network_connect 1
``` 

Prepare the log dir and start httpd if not already running.
If you want to use different log dir name, don't forget to update it in the supervisord config.

```
mkdir /var/log/exafs/
systemctl start httpd
```

#### Supervisord - install as root

Supervisord is used to run and manage applications, but it is not mandatory for deployment.
You can skip this section if you are using a different deployment method, such as Docker.

1. install:
   `pip install supervisor`
2. configure:
   1. `mkdir -p /etc/supervisord/conf.d`
   2. `echo_supervisord_conf > /etc/supervisord/supervisord.conf`
   3. `echo "[include]" >> /etc/supervisord/supervisord.conf`
   4. `echo "files = conf.d/*.conf" >> /etc/supervisord/supervisord.conf`
   
   
3. setup as service:
    `cp docs/supervisor/supervisord.example.service /usr/lib/systemd/system/supervisord.service`
4. copy exafs.supervisord.conf to /etc/supervisord/
  `cp docs/supervisor/exafs.supervisord.conf /etc/supervisord/conf.d/`
5. start service
   `systemctl start supervisord`
6. view service status:
   `systemctl status supervisord`
7. auto start service on system startup: 
   `systemctl enable supervisord`


#### Final steps - as deploy user

1. Copy config.example.py to config.py and fill out the DB credentials.

2. Create and populate database tables (roles, actions, rule states):
```
cd ~/www
source venv/bin/activate
python scripts/db-init.py
```

3. Create the first admin user and organization using the interactive setup script:
```
python scripts/create-admin.py
```
The script will prompt you for the admin's UUID (Shibboleth eppn), name, email, phone, and then create or select an organization with its network address range. It assigns the admin role automatically.

The application is installed and should be working now. The next step is to configure ExaBGP and connect it to the ExaAPI application. We also provide simple service called guarda to reload all the rules in case of ExaBGP restart.

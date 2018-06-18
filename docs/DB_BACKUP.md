# FlowSpec tool
##  MariaDB database backup script

Example of bashscript for database dump and backup. 

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

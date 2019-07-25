# FlowSpec tool
## MariaDB local dev instalation notes

### Show database and tables encoding and collation

```mysql
SELECT default_character_set_name, default_collation_name FROM information_schema.schemata WHERE schema_name = 'exafs';

SHOW table status like '%';
```

### MariaDB character encoding
set utf-8 if needed
```
ALTER DATABASE databasename CHARACTER SET utf8 COLLATE utf8_unicode_ci;
ALTER TABLE tablename CONVERT TO CHARACTER SET utf8 COLLATE utf8_unicode_ci;
```

### Run Mariadb in docker

```
docker run --name=flowspec-db --env="MYSQL_ROOT_PASSWORD=my-secret-pw"  --volume="/home/albert/work/flowspec/datadir:/var/lib/mysql" -p 3306:3306 --restart=no mariadb:5.5 
```
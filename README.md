# Flowspec tool

## Devel config

### Run Mariadb in docker

docker run --name=flowspec-mariadb --env="MYSQL_ROOT_PASSWORD=my-secret-pw" --env="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" --env="GOSU_VERSION=1.7" --env="GPG_KEYS=199369E5404BD5FC7D2FE43BCBCB082A1BB943DB     430BDF5C56E7C94E848EE60C1C4CBDCDCD2EFD2A    4D1BB29D63D98E422B2113B19334A25F8507EFA5" --env="MARIADB_MAJOR=5.5" --env="MARIADB_VERSION=5.5.54+maria-1~wheezy" --volume="/home/albert/work/flowspec/datadir:/var/lib/mysql" --volume="/var/lib/mysql" -p 3306:3306 --restart=no --detach=true mariadb:5.5 mysqld
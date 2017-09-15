# Flowspec tool

## Devel config

### Run Mariadb in docker

'''
docker run --name=flowspec-db --env="MYSQL_ROOT_PASSWORD=my-secret-pw"  --volume="/home/albert/work/flowspec/datadir:/var/lib/mysql" -p 3306:3306 --restart=no mariadb:5.5 
'''
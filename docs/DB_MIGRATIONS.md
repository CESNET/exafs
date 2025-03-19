# How to Upgrade the Database  

## General Guidelines  
Migrations can be inconsistent. To avoid issues, we removed migrations from git repostory. To start the migration on your server, it is recomended reset the migration state on the server and run the migration based on the updated database models when switching application versions via Git.  

```bash
rm -rf migrations/
```

```SQL
DROP TABLE alembic_version;
```

```bash
flask db init
flask db migrate -m "Initial migration based on current DB state"
flask db upgrade
```

## Steps for Upgrading to v1.0.x
Limits for number of rules were introduced. Some database engines (Mariadb 10.x for example) have issue to set Non Null foreigin key to 0 and automatic migrations fail. The solution may be in diferent version (Mariadb 11.x works fine), or to set limits in db manually later.

To set the limit to 0 for existing organizations run

```SQL
UPDATE organization 
SET limit_flowspec4 = 0, limit_flowspec6 = 0, limit_rtbh = 0 
WHERE limit_flowspec4 IS NULL OR limit_flowspec6 IS NULL OR limit_rtbh IS NULL;
```

In all cases we need later assign rules to organizations. There's an admin endpoint for this:  

`https://yourexafs.url/admin/set-org-if-zero`

Or you can start with clean database and manually migrate data by SQL dump later. Feel free to contact jiri.vrany@cesnet.cz if you need help with the DB migration to 1.0.x. 

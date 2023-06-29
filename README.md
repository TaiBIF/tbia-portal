# TBIA portal
This is repository for [TBIA portal](tbiadata.tw).

## Setting docker volumes
create a folder called `tbia-volumes` with following structures:

```
- bucket
- media
    - download
        - record
        - sensitive
        - taxon
    - geojson
    - match_log
    - news
    - resources
```

## Installing 

1. copy `dotenv.example` file and rename it to `.env`
2. start service

```
docker-compose up -d
```


## Setting solr

customize solr config for the first time

```
docker-compose exec solr bash

# in docker shell
cp /workspace/conf-tbia/tbia_records/managed-schema /var/solr/data/tbia_records/conf/
cp /workspace/conf-tbia/tbia_records/solrconfig.xml /var/solr/data/tbia_records/conf/
exit

# restart solr 
docker-compose restart solr
```

## Setting cronjob

see `cronjob.sh`
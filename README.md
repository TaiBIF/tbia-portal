# TBIA portal
This is repository for TBIA portal.

## Solr setup
Download and run solr via docker:
# 需先建立/tbia-volumes/solr/data & /tbia-volumes/solr/csvs
```
$ docker pull solr
$ docker run -d -p 8983:8983 -t solr
$ docker-compose exec -u 0 solr bash
$ cp /workspace/conf-tbia/tbia_records/managed-schema /var/solr/data/tbia_records/conf/
$ cp /workspace/conf-tbia/tbia_records/solrconfig.xml /var/solr/data/tbia_records/conf/
$ cp /workspace/jts-core-1.18.1.jar /opt/solr-8.11.1/server/solr-webapp/webapp/WEB-INF/lib
# 確認jts-core-1.18.1.jar有cp過去再restart
$ docker-compose restart solr
```

Solr Admin:  http://localhost:8983/ 

### import data
```
$ cd /var/solr/csvs
$ post -c tbia_records [filename]
```

# NomenMatch setup
```
$ git clone https://github.com/jinyinglee/NomenMatch.git
```
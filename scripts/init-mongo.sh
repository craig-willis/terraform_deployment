#!/bin/bash


domain=$1
globus_client_id=$2
globus_client_secret=$3

# Wait for wt_mongo1 container
container=$(docker ps -qf label=com.docker.swarm.service.name=wt_mongo1)

i=1
while [ -z "$container" ]; do
  container=$(docker ps -qf label=com.docker.swarm.service.name=wt_mongo1)
  echo "Waiting for wt_mongo1 to start (retry $i)"
  sleep 30
  ((i++))
  if [ $i -gt 10 ]; then
     echo "Timeout waiting for wt_mongo1"
     exit 1;
  fi
done


# Init replica set
echo "Initializing replica set"
docker exec -it $container mongo --eval 'rs.initiate( { _id : "rs1", members: [ { _id : 0, host : "wt_mongo1:27017" } ] })'

# Create replica set
echo "Configuring replica set"
docker exec -it $container mongo --eval 'rs.add("wt_mongo2:27017"); rs.add("wt_mongo3:27017")'


# Update CORS origin
if [ ! -z "$domain" ]; then
   echo "Adding $domain to Girder CORS origin"
   docker exec $container mongo girder --eval 'db.setting.updateOne( { key: "core.cors.allow_origin" }, { $set : { value: "http://localhost:4200, https://dashboard.wholetale.org, http://localhost:8000, https://dashboard-dev.wholetale.org, https://dashboard.'$domain'"}})'
fi

docker exec $container mongo girder --eval 'db.assetstore.updateOne( { name: "GridFS local" }, { $set : { mongohost: "mongodb://wt_mongo1:27017,wt_mongo2:27017,wt_mongo3:27017"}})'

# Update Globus keys
if [ ! -z "$globus_client_id" ]; then
   echo "Updating Globus client ID and secret"
   docker exec $container mongo girder --eval 'db.setting.updateOne( { key : "oauth.globus_client_id" }, { $set: { value: "'$globus_client_id'"} } )'
   docker exec $container mongo girder --eval 'db.setting.updateOne( { key : "oauth.globus_client_secret" }, { $set: { value: "'$globus_client_secret'"} } )'
   docker exec $container mongo girder --eval 'db.setting.find()'
fi

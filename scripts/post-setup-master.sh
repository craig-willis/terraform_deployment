#!/bin/bash

mtu=$1

# Create a default swarm bridge with proper MTU
echo "Removing ingress network"
echo "y" | docker network rm ingress <&0
sleep 5

echo "Listing networks"
docker network ls

echo "Creating ingress network"
docker network create \
  -d overlay \
  --ingress \
  --opt com.docker.network.driver.mtu=${mtu} \
  ingress



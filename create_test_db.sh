#!/bin/sh

IMAGE_NAME="docker.io/mysql"
CONTAINER_NAME="mysql-instance"

. ./default_env.sh

if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then

   docker start "$CONTAINER_NAME"

else 

   docker run \
      --name "$CONTAINER_NAME" \
      -p 127.0.0.1:3306:3306 \
      -e MYSQL_DATABASE="$DB_NAME" \
      -e MYSQL_ROOT_PASSWORD="$DB_PASSWORD" \
      -d \
      "$IMAGE_NAME"
fi


if [ -d ./py_core ]; then

   cd py_core
   
   alembic ensure_version
   
   if ! alembic check; then
   
      echo "Running database migrations"
   
      alembic upgrade head
   
   fi
   
fi
#!/bin/sh

log_dir="$HOME/log/jenkins-ssh"
mkdir -p $log_dir

log_file="$log_dir/dataScrape-dockerrun-log.out"
touch log_file

exec 3>&1 4>&2
trap 'exec 2>&4 1>&3' 0 1 2 3
exec 1>$log_file 2>&1

container_name="dScrape-Instance"

echo "Stopping container..."

docker stop $container_name || true

while [ "$(docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null)" = "true" ]; do
    echo "Waiting for container to stop..."
    sleep 1
done

echo "Running build..."

docker run -itd --rm --network EZnet --name $container_name dscrape

echo "Deploy done."

#!/bin/sh

log_dir="$HOME/log/jenkins-ssh"
mkdir -p $log_dir

log_file="$log_dir/dataScrape-dockerbuild-log.out"
touch log_file

exec 3>&1 4>&2
trap 'exec 2>&4 1>&3' 0 1 2 3
exec 1>$log_file 2>&1


chmod +x entrypoint.sh

docker build -t dscrape .


#!/bin/sh
# Copyright (C) 2022-2023 EZCampus 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


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

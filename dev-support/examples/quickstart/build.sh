#!/usr/bin/env bash
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euxo pipefail

SUBMARINE_VERSION=v0.0.1
SUBMARINE_IMAGE_NAME="harbor.nodefans.cn:8443/submarine/quickstart:${SUBMARINE_VERSION}"

if [ -L ${BASH_SOURCE-$0} ]; then
  PWD=$(dirname $(readlink "${BASH_SOURCE-$0}"))
else
  PWD=$(dirname ${BASH_SOURCE-$0})
fi
export CURRENT_PATH=$(cd "${PWD}">/dev/null; pwd)
export SUBMARINE_HOME=${CURRENT_PATH}/../../..

if [ -d "${CURRENT_PATH}/tmp" ] # if old tmp folder is still there, delete it.
then
  rm -rf "${CURRENT_PATH}/tmp"
fi

mkdir -p "${CURRENT_PATH}/tmp"
cp -r "${SUBMARINE_HOME}/submarine-sdk" "${CURRENT_PATH}/tmp"

# build image
cd ${CURRENT_PATH}
echo "Start building the ${SUBMARINE_IMAGE_NAME} docker image ..."
docker build --add-host storage.googleapis.com:172.217.160.112 -t ${SUBMARINE_IMAGE_NAME} .

# clean temp file
rm -rf "${CURRENT_PATH}/tmp"

#!/bin/bash

# This script will install dependencies to run the test Techtile software


if [ $(id -u) != "0" ]; then
echo "You must be the superuser to run this script" >&2
exit 1
fi
apt -y update

apt -y upgrade

# Install the build tools (dpkg-dev g++ gcc libc6-dev make)
apt -y install build-essential cmake pkg-config

# Install UHD
apt -y install libuhd-dev uhd-host

# Install ZMQ
apt -y install libzmq3-dev

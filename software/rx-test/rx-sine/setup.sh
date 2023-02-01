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

# Install git
apt -y install git

# Clone this project
sudo -u pi git clone https://github.com/techtile-by-dramco/NI-B210-Sync.git

# if you want to push use this to set remote "git remote set-url origin https://<auth-token>@github.com/techtile-by-dramco/NI-B210-Sync.git"
# increase buffersize
git config --global http.postBuffer 524288000



# Navigate to software folder and build
cd NI-B210-Sync/software/rx-test/rx-zc
sudo -u pi mkdir build
cd build
cmake ..
make

# UHD install FPGA images for UHD
/usr/lib/uhd/utils/uhd_images_downloader.py
echo "export UHD_IMAGES_DIR=/usr/share/uhd/images" >> ~/.bashrc

cp /usr/lib/uhd/utils/uhd-usrp.rules /etc/udev/rules.d/
udevadm control --reload-rules
udevadm trigger

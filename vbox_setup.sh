#!/bin/bash

apt-get update
apt-get install -y python-setuptools vim
easy_install pip
pip install virtualenvwrapper

# Build the bash_profile
echo "source ~/.profile" >> /home/vagrant/.bash_profile
echo "source /usr/local/bin/virtualenvwrapper.sh" >> /home/vagrant/.bash_profile

chown vagrant:vagrant /home/vagrant/.bash_profile

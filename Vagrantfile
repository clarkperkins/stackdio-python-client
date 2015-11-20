# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "precise64"

  config.vm.provision "shell", path: "vbox_setup.sh"

  config.vm.synced_folder "~/Workspace/pi/stackdio-blueprints", "/home/vagrant/.stackdio-blueprints", create: true
end

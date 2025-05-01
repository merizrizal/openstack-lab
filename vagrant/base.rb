# -*- mode: ruby -*-
# vi: set ft=ruby :

require "yaml"

def setup_vm(component, config, box_name, shell_command)
  inventories = get_inventories(component)

  config.vm.box = box_name
  config.ssh.username = "vagrant"
  config.ssh.password = "vagrant"

  customize_vms(config, inventories)
  resize_disk(config)

  if !shell_command.nil?
    config.vm.provision "shell", inline: shell_command
  end

  inventories.each do |host, inventory|
    config.vm.define host do |machine|
      set_hostname(machine)
      provision(machine)
    end
  end

  initialize = ENV["INITIALIZE"]
  if initialize.nil?
    inventories.each do |host, inventory|
      config.vm.define host do |machine|
        machine.ssh.host = inventory["private_ip_address"]
      end
    end
  end
end

def get_inventories(component)
  inventories = YAML.load_file "#{ENV["ROOT_DIR"]}/inventories/#{component}"

  return inventories
end

def customize_vms(config, inventories)
  inventories.each do |host, inventory|
    config.vm.define host do |machine|
      machine.vm.hostname = inventory["hostname"]
      machine.vm.synced_folder ".", "/vagrant", disabled: true
      machine.vm.network "public_network", ip: inventory["provider_ip_address"],
        dev: "br-provider0", mode: "bridge", type: "bridge"
      machine.vm.network "private_network", ip: inventory["private_ip_address"]
      machine.vm.provider "libvirt" do |lv|
        lv.memory = inventory["memory"]
        lv.cpus = inventory["cpus"]
        lv.machine_virtual_size = inventory["disks"]
        lv.qemu_use_agent = true

        if !inventory["additional_disks"].nil?
          inventory["additional_disks"].each do |disks|
            lv.storage :file, size: "#{disks}G", device: "vdb"
          end
        end
      end
    end
  end
end

def resize_disk(config)
  config.vm.provision "shell", inline: <<-SHELL
    printf "\nDisk free space before...\n"
    df -lhT /

    part_nr=$(lsblk --path --pairs | sed 's/\"//g' | awk '/\\/dev\\/vda/{print $1}' | awk -F '/dev/vda' '{print $2}' | tail -n 1)
    device=$(df -lhT / | awk '/\\/dev/{print $1}')
    check_type=$(lsblk --pairs | grep -E 'MOUNTPOINT*.*="/"' | sed 's/\"//g')

    printf "\nResizing / partition live...\n"
    printf "/dev/vda $part_nr ...\n"

    growpart /dev/vda $part_nr
    if [[ "$check_type" == *"TYPE=part"* ]]; then
      printf "Found TYPE=part disk...\n"
    elif [[ "$check_type" == *"TYPE=lvm"* ]]; then
      printf "Found TYPE=lvm disk...\n"
      pvresize /dev/vda$part_nr
      lvresize -l +100%FREE $device
    fi

    check_fstype=$(lsblk --pairs --fs | grep -E 'MOUNTPOINT*.*="/"' | sed 's/\"//g')

    if [[ "$check_fstype" == *"FSTYPE=ext4"* ]]; then
      resize2fs $device
    elif [[ "$check_fstype" == *"FSTYPE=xfs"* ]]; then
      xfs_growfs $device
    fi

    printf "\nDisk free space after...\n"
    df -lhT /
  SHELL
end

def set_hostname(machine)
  inventories = get_inventories("local/nodes.yml")
  inventories.each do |key, value|
    machine.vm.provision "shell" do |s|
      ip_addr_hostname = "#{value["mgmtnet_ip_address"]} #{value["hostname"]}"
      s.inline = <<-SHELL
        echo "Set #{ip_addr_hostname}"
        sudo echo "#{ip_addr_hostname}" | sudo tee -a /etc/hosts
      SHELL
    end
  end
end

def provision(machine)
  provision_src = YAML.load_file "./provision.yml"
  inventories = get_inventories("local/nodes.yml")
  inventories.each do |key, value|
    machine.vm.provision "shell" do |s|
      provision_cmds = provision_src[value["environment"]]
      s.inline = <<-SHELL
        #{provision_cmds}
      SHELL
    end
  end
end

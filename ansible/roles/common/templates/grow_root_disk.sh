printf "\nDisk free space before...\n"
df -lhT /

part_nr=$(lsblk --path --pairs | sed 's/\"//g' | awk '/\/dev\/sda/{print $1}' | awk -F '/dev/sda' '{print $2}' | tail -n 1)
device=$(df -lhT / | awk '/\/dev/{print $1}')
check_type=$(lsblk --pairs | grep -E 'MOUNTPOINT*.*="/"' | sed 's/\"//g')

printf "\nResizing / partition live...\n"
printf "/dev/sda $part_nr ...\n"

growpart /dev/sda $part_nr
if [[ "$check_type" == *"TYPE=part"* ]]; then
  printf "Found TYPE=part disk...\n"
elif [[ "$check_type" == *"TYPE=lvm"* ]]; then
  printf "Found TYPE=lvm disk...\n"
  pvresize /dev/sda$part_nr
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
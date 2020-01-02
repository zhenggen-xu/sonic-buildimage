#!/bin/bash

#platform init script for Dell S6100

source dell_i2c_utils.sh

init_devnum() {
    found=0
    for devnum in 0 1; do
        devname=`cat /sys/bus/i2c/devices/i2c-${devnum}/name`
        # iSMT adapter can be at either dffd0000 or dfff0000
        if [[ $devname == 'SMBus iSMT adapter at '* ]]; then
            found=1
            break
        fi
    done

    [[ $found -eq 0 ]] && echo "cannot find iSMT" && exit 1
}

# Attach/Detach CPU board mux @ 0x70
cpu_board_mux() {
    case $1 in
        "new_device")    i2c_mux_create pca9547 0x70 $devnum 2 
                         ;;
        "delete_device") i2c_mux_delete 0x70 $devnum
                         ;;
        *)               echo "s6100_platform: cpu_board_mux: invalid command !"
                         ;;
    esac
}

# Attach/Detach Switchboard MUX @ 0x71
switch_board_mux() {
    case $1 in
        "new_device")    i2c_mux_create pca9548 0x71 4 10
                         ;;
        "delete_device") i2c_mux_delete 0x71 4
                         ;;
        *)               echo "s6100_platform: switch_board_mux : invalid command !"
                         ;;
    esac
}

# Attach/Detach syseeprom on CPU board
sys_eeprom() {
    case $1 in
        "new_device")    i2c_config "echo 24c02 0x50 > /sys/bus/i2c/devices/i2c-2/$1"
                         ;;
        "delete_device") i2c_config "echo 0x50 > /sys/bus/i2c/devices/i2c-2/$1"
                         ;;
        *)               echo "s6100_platform: sys_eeprom : invalid command !"
                         ;;
    esac
}

#Attach/Detach eeprom on each IOM
switch_board_eeprom() {
    case $1 in
        "new_device")
                      for ((i=14;i<=17;i++));
                      do
                          i2c_config "echo 24c02 0x50 > /sys/bus/i2c/devices/i2c-$i/$1"
                      done
                      ;;
        "delete_device")
                      for ((i=14;i<=17;i++));
                      do
                          i2c_config "echo 0x50 > /sys/bus/i2c/devices/i2c-$i/$1"
                      done
                      ;;
        *)            echo "s6100_platform: switch_board_eeprom : invalid command !"
                      ;;
    esac
}

#Attach/Detach CPLD devices to drivers for each IOM
switch_board_cpld() {
    case $1 in
        "new_device")    
                      for ((i=14;i<=17;i++));
                      do
                          i2c_config "echo  dell_s6100_iom_cpld 0x3e > /sys/bus/i2c/devices/i2c-$i/$1"
                      done
                      ;;
        "delete_device")
                      for ((i=14;i<=17;i++));
                      do
                          i2c_config "echo  0x3e > /sys/bus/i2c/devices/i2c-$i/$1"
                      done
                      ;;
        *)            echo "s6100_platform: switch_board_cpld : invalid command !"
                      ;;
    esac
}

#Attach/Detach the MUX connecting all QSFPs on each IOM @0x71 and 0x72
switch_board_qsfp_mux() {
    case $1 in
        "new_device")
                      # The mux for the QSFPs spawn {18..25}, {26..33}... {74..81}
                      # starting at chennel 18 and 16 channels per IOM.
                      channel_first=18
                      for ((i=9;i>=6;i--));
                      do
                          # 0x71 mux on the IOM 1
                          mux_index=$(expr $i - 5)
                          echo "Attaching PCA9548 $mux_index"
                          i2c_mux_create pca9548 0x71 $i $channel_first
                          i2c_mux_create pca9548 0x72 $i $(expr $channel_first + 8)
                          channel_first=$(expr $channel_first + 16)
                      done
                      ;;
        "delete_device")
                      for ((i=9;i>=6;i--));
                      do
                          # 0x71 mux on the IOM 1
                          mux_index=$(expr $i - 5)
                          echo "Detaching PCA9548 $mux_index"
                          i2c_mux_delete 0x71 $i
                          i2c_mux_delete 0x72 $i
                      done
                      ;;
        *)            echo "s6100_platform: switch_board_qsfp_mux: invalid command !"
                      ;;
    esac
}

#Attach/Detach the SFP modules on PCA9548_2
switch_board_sfp() {
    case $1 in
        "new_device")    i2c_config "echo optoe2 0x50 > /sys/bus/i2c/devices/i2c-11/$1"
                         i2c_config "echo optoe2 0x50 > /sys/bus/i2c/devices/i2c-12/$1"
                         ;;
        "delete_device") i2c_config "echo 0x50 > /sys/bus/i2c/devices/i2c-11/$1"
                         i2c_config "echo 0x50 > /sys/bus/i2c/devices/i2c-12/$1"
                         ;;
        *)               echo "s6100_platform: switch_board_sfp: invalid command !"
                         ;;
    esac
}

#Add/Delete ($1) a range ($2..$3) of QSFPs
qsfp_device_mod() {
    case $1 in
        "new_device")    for ((i=$2;i<=$3;i++));
                         do
                             i2c_config "echo optoe1 0x50 > /sys/bus/i2c/devices/i2c-$i/$1"
                         done
                         ;;
        "delete_device") for ((i=$2;i<=$3;i++));
                         do
                             i2c_config "echo 0x50 > /sys/bus/i2c/devices/i2c-$i/$1"
                         done
                         ;;
        *)              echo "s6100_platform: qsfp_device_mod: invalid command $1:$2,$3!"
                        ;;
    esac
}

# Attach/Detach 16 instances of QSFP ports on each IO modules
# eeprom can dump data using below command
switch_board_qsfp() {
    if  i2c_poll_bus_exists  "/sys/bus/i2c/devices/i2c-18"; then
        qsfp_device_mod $1 18 33
    fi

    if  i2c_poll_bus_exists  "/sys/bus/i2c/devices/i2c-34"; then
        qsfp_device_mod $1 34 49
    fi

    if  i2c_poll_bus_exists  "/sys/bus/i2c/devices/i2c-50"; then
        qsfp_device_mod $1 50 65
    fi

    if  i2c_poll_bus_exists  "/sys/bus/i2c/devices/i2c-66"; then
        qsfp_device_mod $1 66 81
    fi
}

# Enable/Disable low power mode on all QSFP ports
switch_board_qsfp_lpmode() {
    case $1 in
        "enable")   value=0xffff
                    ;;
        "disable")  value=0x0
                    ;;
        *)          echo "s6100_platform: switch_board_qsfp_lpmode: invalid command $1!"
                    return
                    ;;
    esac
    echo $value > /sys/class/i2c-adapter/i2c-14/14-003e/qsfp_lpmode
    echo $value > /sys/class/i2c-adapter/i2c-15/15-003e/qsfp_lpmode
    echo $value > /sys/class/i2c-adapter/i2c-16/16-003e/qsfp_lpmode
    echo $value > /sys/class/i2c-adapter/i2c-17/17-003e/qsfp_lpmode
}

# Enable/Disable xcvr presence interrupts
xcvr_presence_interrupts() {
    case $1 in
        "enable")
                      for ((i=14;i<=17;i++));
                      do
                          echo 0x0 > /sys/class/i2c-adapter/i2c-$i/$i-003e/qsfp_abs_mask
                      done
                      ;;
        "disable")
                      for ((i=14;i<=17;i++));
                      do
                          echo 0xffff > /sys/class/i2c-adapter/i2c-$i/$i-003e/qsfp_abs_mask
                      done
                      ;;
        *)            echo "s6100_platform: xcvr_presence_interrupts: invalid command !"
                      ;;
    esac
}

# Reset the mux tree
reset_muxes() {
    local i

    # Reset the IOM muxes (if they have been already instantiated)
    for ((i=14;i<=17;i++));
    do
        if [[ -e /sys/class/i2c-adapter/i2c-$i/$i-003e ]]; then
            echo 0xfc > /sys/class/i2c-adapter/i2c-$i/$i-003e/sep_reset
            echo 0xff > /sys/class/i2c-adapter/i2c-$i/$i-003e/sep_reset
        fi
    done

    # Reset the switch card PCA9548A
    io_rd_wr.py --set --val 0xef --offset 0x110
    io_rd_wr.py --set --val 0xff --offset 0x110

    # Reset the CPU Card PCA9547
    io_rd_wr.py --set --val 0xfd --offset 0x20b
    io_rd_wr.py --set --val 0xff --offset 0x20b
}

track_reboot_reason() {
    if [[ -d /sys/devices/platform/SMF.512/hwmon/ ]]; then
        rv=$(cd /sys/devices/platform/SMF.512/hwmon/*; cat mb_poweron_reason)
        reason=$(echo $rv | cut -d 'x' -f2)
        if [ $reason == "ff" ]; then
            cd /sys/devices/platform/SMF.512/hwmon/*
            if [[ -e /tmp/notify_firstboot_to_platform ]]; then
                echo 0x01 > mb_poweron_reason
            else
                echo 0xbb > mb_poweron_reason
            fi
        elif [ $reason == "bb" ] || [ $reason == "1" ]; then
            cd /sys/devices/platform/SMF.512/hwmon/*
            echo 0xaa > mb_poweron_reason
        fi
    fi
}

install_python_api_package() {
    device="/usr/share/sonic/device"
    platform=$(/usr/local/bin/sonic-cfggen -H -v DEVICE_METADATA.localhost.platform)

    rv=$(pip install $device/$platform/sonic_platform-1.0-py2-none-any.whl)
}

remove_python_api_package() {
    rv=$(pip show sonic-platform > /dev/null 2>/dev/null)
    if [ $? -eq 0 ]; then
        rv=$(pip uninstall -y sonic-platform > /dev/null 2>/dev/null)
    fi
}

init_devnum

if [[ "$1" == "init" ]]; then
    modprobe i2c-dev
    modprobe i2c-mux-pca954x force_deselect_on_exit=1
    modprobe dell_ich
    modprobe dell_s6100_iom_cpld
    modprobe dell_s6100_lpc
    track_reboot_reason

    # Disable Watchdog Timer
    if [[ -e /usr/local/bin/platform_watchdog_disable.sh ]]; then
        /usr/local/bin/platform_watchdog_disable.sh
    fi

    cpu_board_mux "new_device"
    switch_board_mux "new_device"
    sys_eeprom "new_device"
    switch_board_eeprom "new_device"
    switch_board_cpld "new_device"
    switch_board_qsfp_mux "new_device"
    switch_board_sfp "new_device"
    switch_board_qsfp "new_device"
    switch_board_qsfp_lpmode "disable"
    xcvr_presence_interrupts "enable"

    install_python_api_package

elif [[ "$1" == "deinit" ]]; then
    xcvr_presence_interrupts "disable"
    switch_board_sfp "delete_device"
    switch_board_cpld "delete_device"
    switch_board_eeprom "delete_device"
    switch_board_mux "delete_device"
    sys_eeprom "delete_device"
    switch_board_qsfp "delete_device"
    switch_board_qsfp_mux "delete_device"
    cpu_board_mux "delete_device"

    modprobe -r dell_s6100_lpc
    modprobe -r dell_s6100_iom_cpld
    modprobe -r i2c-mux-pca954x
    modprobe -r i2c-dev
    modprobe -r dell_ich
    remove_python_api_package
else
     echo "s6100_platform : Invalid option !"
fi

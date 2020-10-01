#!/bin/bash

ntp_default_file='/etc/default/ntp'
ntp_temp_file='/tmp/ntp.orig'

reboot_type='cold'

function get_database_reboot_type()
{
    SYSTEM_WARM_START=`/usr/bin/redis-cli -n 6 hget "WARM_RESTART_ENABLE_TABLE|system" enable`
    SYSTEM_FAST_START=`/usr/bin/redis-cli -n 6 get "FAST_REBOOT|system"`

    if [[ x"${SYSTEM_WARM_START}" == x"true" ]]; then
        reboot_type='warm'
    elif [[ x"${SYSTEM_FAST_START}" == x"1" ]]; then
        reboot_type='fast'
    fi
}

function modify_ntp_default
{
    cp ${ntp_default_file} ${ntp_temp_file}
    sed -e "$1" ${ntp_temp_file} >${ntp_default_file}
}

sonic-cfggen -d -t /usr/share/sonic/templates/ntp.conf.j2 >/etc/ntp.conf

get_database_reboot_type
echo "Disabling NTP long jump for reboot type ${reboot_type} ..."
modify_ntp_default "s/NTPD_OPTS='-g'/NTPD_OPTS='-x'/"

systemctl restart ntp

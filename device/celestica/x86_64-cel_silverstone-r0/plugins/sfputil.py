#!/usr/bin/env python
#
# Platform-specific SFP transceiver interface for SONiC
# This plugin supports QSFP-DD, QSFP and SFP.

try:
    import time
    import subprocess
    from sonic_platform_base.sonic_sfp.sfputilbase import SfpUtilBase
    from sonic_platform_base.sonic_sfp.sff8024 import type_of_transceiver
    from sonic_platform_base.sonic_sfp.sff8472 import sff8472InterfaceId, sff8472Dom
    from sonic_platform_base.sonic_sfp.sff8436 import sff8436InterfaceId, sff8436Dom
    from sonic_platform_base.sonic_sfp.inf8628 import inf8628InterfaceId
    from sonic_platform_base.sonic_sfp.qsfp_dd import qsfp_dd_InterfaceId, qsfp_dd_Dom
    from sonic_platform_base.sonic_sfp.sffbase import sffbase
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


PLATFORM_ROOT_PATH = '/usr/share/sonic/device'
SONIC_CFGGEN_PATH = '/usr/local/bin/sonic-cfggen'
HWSKU_KEY = 'DEVICE_METADATA.localhost.hwsku'
PLATFORM_KEY = 'DEVICE_METADATA.localhost.platform'


class QSFPDDDomPaser(qsfp_dd_Dom):

    def __init__(self, eeprom_raw_data):

        start_pos = 0
        dom_offset = 256

        dom_module_monitor_values = {
            'Temperature':
                {'offset': 14,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_temperature}},
            'Vcc':
                {'offset': 16,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_voltage}}
        }

        dom_channel_monitor_params = {
            'RX8Power':
                {'offset': 72 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_rx_power}},
            'RX7Power':
                {'offset': 70 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_rx_power}},
            'RX6Power':
                {'offset': 68 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_rx_power}},
            'RX5Power':
                {'offset': 66 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_rx_power}},
            'RX4Power':
                {'offset': 64 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_rx_power}},
            'RX3Power':
                {'offset': 62 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_rx_power}},
            'RX2Power':
                {'offset': 60 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_rx_power}},
            'RX1Power':
                {'offset': 58 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_rx_power}},
            'TX8Bias':
                {'offset': 56 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_bias}},
            'TX7Bias':
                {'offset': 54 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_bias}},
            'TX6Bias':
                {'offset': 52 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_bias}},
            'TX5Bias':
                {'offset': 50 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_bias}},
            'TX4Bias':
                {'offset': 48 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_bias}},
            'TX3Bias':
                {'offset': 46 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_bias}},
            'TX2Bias':
                {'offset': 44 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_bias}},
            'TX1Bias':
                {'offset': 42 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_bias}},
            'TX8Power':
                {'offset': 40 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_tx_power}},
            'TX7Power':
                {'offset': 38 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_tx_power}},
            'TX6Power':
                {'offset': 36 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_tx_power}},
            'TX5Power':
                {'offset': 34 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_tx_power}},
            'TX4Power':
                {'offset': 32 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_tx_power}},
            'TX3Power':
                {'offset': 30 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_tx_power}},
            'TX2Power':
                {'offset': 28 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_tx_power}},
            'TX1Power':
                {'offset': 26 + dom_offset,
                 'size': 2,
                 'type': 'func',
                 'decode': {'func': qsfp_dd_Dom.calc_tx_power}}
        }

        dom_map = {
            'ModuleMonitorValues':
                {'type': 'nested',
                 'decode': dom_module_monitor_values},
            'ChannelMonitorValues':
                {'type': 'nested',
                 'decode': dom_channel_monitor_params}
        }

        self.dom_data = sffbase.parse(
            self, dom_map, eeprom_raw_data, start_pos)

    def get_data_pretty(self):
        return sffbase.get_data_pretty(self, self.dom_data)


class SfpEvent:
    ''' Listen to insert/remove sfp events '''

    PATH_INT_SYSFS = "{0}/{port_name}/qsfp_isr_flags"
    PATH_INTMASK_SYSFS = "{0}/{port_name}/qsfp_isr_mask"
    PATH_PRS_SYSFS = "{0}/{port_name}/qsfp_modprs"
    PRESENT_EN = 0x01

    def __init__(self, num_port, port_info_path):
        self.num_sfp = num_port
        self.port_info_path = port_info_path
        self.__initialize_interrupts()

    def __initialize_interrupts(self):
        # Initial Interrupt MASK for QSFP, SFP
        sfp_info_obj = {}

        for index in range(self.num_sfp):
            port_num = index + 1
            port_name = "QSFP{}".format(port_num)

            sfp_info_obj[index] = {}
            sfp_info_obj[index]['intmask_sysfs'] = self.PATH_INTMASK_SYSFS.format(
                self.port_info_path,
                port_name=port_name)

            sfp_info_obj[index]['int_sysfs'] = self.PATH_INT_SYSFS.format(
                self.port_info_path,
                port_name=port_name)

            sfp_info_obj[index]['prs_sysfs'] = self.PATH_PRS_SYSFS.format(
                self.port_info_path,
                port_name=port_name)

            self._write_file(
                sfp_info_obj[index]["intmask_sysfs"], hex(self.PRESENT_EN))

        self.sfp_info_obj = sfp_info_obj

    def _write_file(self, file_path, data):
        try:
            with open(file_path, 'w') as fd:
                fd.write(str(data))
                return True
        except Exception as e:
            print "Error: unable to read file: %s" % str(e)
        return False

    def _read_txt_file(self, file_path):
        try:
            with open(file_path, 'r') as fd:
                data = fd.read()
                return data.strip()
        except IOError as e:
            print "Error: unable to read file: %s" % str(e)
        return None

    def _port_present_status(self, port_idx):
        prs_path = self.sfp_info_obj[port_idx]["prs_sysfs"]
        prs_val = int(self._read_txt_file(prs_path))
        return 1 - prs_val

    def _clear_event_flag(self, path):
        self._write_file(path, hex(0xff))
        time.sleep(0.1)
        self._write_file(path, hex(0x0))

    def update_port_event_object(self, interrup_devices, port_dict):
        for port_idx in interrup_devices:
            device_id = str(port_idx + 1)
            port_dict[device_id] = str(self._port_present_status(port_idx))
        return port_dict

    def check_all_port_interrupt_event(self):
        interrupt_devices = {}
        for i in range(self.num_sfp):
            int_sysfs = self.sfp_info_obj[i]["int_sysfs"]
            interrupt_flags = self._read_txt_file(int_sysfs)
            if interrupt_flags == '0x01':
                interrupt_devices[i] = 1
                self._clear_event_flag(int_sysfs)
        return interrupt_devices


class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 1
    PORT_END = 34
    OSFP_PORT_START = 1
    OSFP_PORT_END = 32
    SFP_PORT_START = 33
    SFP_PORT_END = 34

    NUM_OSFP = 32

    EEPROM_OFFSET = 9
    PORT_INFO_PATH = '/sys/class/silverstone_fpga'
    QSFP_DD_DOM_OFFSET = 2304

    # polling interval in seconds
    POLL_INTERVAL = 1

    _port_name = ""
    _port_to_eeprom_mapping = {}
    _port_to_i2cbus_mapping = {}

    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_ports(self):
        return []

    @property
    def osfp_ports(self):
        return range(self.OSFP_PORT_START, self.OSFP_PORT_END + 1)

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    @property
    def port_to_i2cbus_mapping(self):
        return self._port_to_i2cbus_mapping

    def get_port_name(self, port_num):
        if port_num in self.osfp_ports:
            self._port_name = "QSFP" + str(port_num - self.OSFP_PORT_START + 1)
        else:
            self._port_name = "SFP" + str(port_num - self.SFP_PORT_START + 1)
        return self._port_name

    def get_eeprom_dom_raw(self, port_num):
        if port_num in self.osfp_ports:
            # QSFP DOM EEPROM is also at addr 0x50 and thus also stored in eeprom_ifraw
            return self._read_eeprom_devid(port_num, self.IDENTITY_EEPROM_ADDR, self.QSFP_DD_DOM_OFFSET, 128)
        else:
            # Read dom eeprom at addr 0x51
            return self._read_eeprom_devid(port_num, self.DOM_EEPROM_ADDR, 256)

    def __init__(self):
        # Override port_to_eeprom_mapping for class initialization
        eeprom_path = '/sys/bus/i2c/devices/i2c-{0}/{0}-0050/eeprom'

        for x in range(self.PORT_START, self.PORT_END+1):
            self.port_to_i2cbus_mapping[x] = (x + self.EEPROM_OFFSET)
            self.port_to_eeprom_mapping[x] = eeprom_path.format(
                x + self.EEPROM_OFFSET)
        SfpUtilBase.__init__(self)

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num not in range(self.port_start, self.port_end + 1):
            return False

        # Get path for access port presence status
        port_name = self.get_port_name(port_num)
        sysfs_filename = "qsfp_modprs" if port_num in self.osfp_ports else "sfp_modabs"
        reg_path = "/".join([self.PORT_INFO_PATH, port_name, sysfs_filename])

        # Read status
        try:
            reg_file = open(reg_path)
            content = reg_file.readline().rstrip()
            reg_value = int(content)
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        # Module present is active low
        if reg_value == 0:
            return True

        return False

    def get_low_power_mode(self, port_num):
        # Check for invalid QSFP port_num
        if port_num not in self.osfp_ports:
            return False

        try:
            port_name = self.get_port_name(port_num)
            reg_file = open("/".join([self.PORT_INFO_PATH,
                                      port_name, "qsfp_lpmode"]))
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        # Read status
        content = reg_file.readline().rstrip()
        reg_value = int(content)
        # low power mode is active high
        if reg_value == 0:
            return False

        return True

    def set_low_power_mode(self, port_num, lpmode):
        # Check for invalid QSFP port_num
        if port_num not in self.osfp_ports:
            return False

        try:
            port_name = self.get_port_name(port_num)
            reg_file = open("/".join([self.PORT_INFO_PATH,
                                      port_name, "qsfp_lpmode"]), "r+")
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        content = hex(lpmode)

        reg_file.seek(0)
        reg_file.write(content)
        reg_file.close()

        return True

    def reset(self, port_num):
        # Check for invalid QSFP port_num
        if port_num not in self.osfp_ports:
            return False

        try:
            port_name = self.get_port_name(port_num)
            reg_file = open("/".join([self.PORT_INFO_PATH,
                                      port_name, "qsfp_reset"]), "w")
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        # Convert our register value back to a hex string and write back
        reg_file.seek(0)
        reg_file.write(hex(0))
        reg_file.close()

        # Sleep 1 second to allow it to settle
        time.sleep(1)

        # Flip the bit back high and write back to the register to take port out of reset
        try:
            reg_file = open(
                "/".join([self.PORT_INFO_PATH, port_name, "qsfp_reset"]), "w")
        except IOError as e:
            print "Error: unable to open file: %s" % str(e)
            return False

        reg_file.seek(0)
        reg_file.write(hex(1))
        reg_file.close()

        return True

    def _run_command(self, cmd, time=1):
        for i in range(time):
            p = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if p.returncode != 0:
                continue
            return p.communicate()[0].strip()
        return

    def _init_cmis_module(self, int_sfp, init_script):
        # Workaround script for cmis module
        for port_num in int_sfp:
            # Check if it's the module insert event.
            if int_sfp[port_num] == '1':
                i2c_num = int(port_num) + self.EEPROM_OFFSET

                # run cmis init script
                init_cmd = "bash {} {}".format(init_script, i2c_num)
                self._run_command(init_cmd, 3)

    def _get_platform_and_hwsku(self):
        try:
            proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-H', '-v', PLATFORM_KEY],
                                    stdout=subprocess.PIPE,
                                    shell=False,
                                    stderr=subprocess.STDOUT)
            stdout = proc.communicate()[0]
            proc.wait()
            platform = stdout.rstrip('\n')

            proc = subprocess.Popen([SONIC_CFGGEN_PATH, '-d', '-v', HWSKU_KEY],
                                    stdout=subprocess.PIPE,
                                    shell=False,
                                    stderr=subprocess.STDOUT)
            stdout = proc.communicate()[0]
            proc.wait()
            hwsku = stdout.rstrip('\n')
        except OSError, e:
            raise OSError("Cannot detect platform")

        return (platform, hwsku)

    def get_path_to_cmis_init_file(self):
        (platform, hwsku) = self._get_platform_and_hwsku()
        platform_path = "/".join([PLATFORM_ROOT_PATH, platform])
        hwsku_path = "/".join([platform_path, hwsku])
        cmis_init_file_path = "/".join([hwsku_path, "cmis-init.sh"])
        return cmis_init_file_path

    def get_transceiver_change_event(self, timeout=0):
        """
        :param timeout in milliseconds. The method is a blocking call. When timeout is 
         zero, it only returns when there is change event, i.e., transceiver plug-in/out
         event. When timeout is non-zero, the function can also return when the timer expires.
         When timer expires, the return status is True and events is empty.
        :returns: (status, events)
        :status: Boolean, True if call successful and no system level event/error occurred, 
         False if call not success or system level event/error occurred.
        :events: dictionary for physical port index and the SFP status,
         status='1' represent plug in, '0' represent plug out like {'0': '1', '31':'0'}
         when it comes to system level event/error, the index will be '-1',
         and status can be 'system_not_ready', 'system_become_ready', 'system_fail',
         like {'-1':'system_not_ready'}.
        """
        cmis_init_script = self.get_path_to_cmis_init_file()
        sfp_event = SfpEvent(self.NUM_OSFP, self.PORT_INFO_PATH)
        start_milli_time = int(round(time.time() * 1000))
        timeout_in_sec = timeout/1000.0
        int_sfp = {}

        sleep_time = min(
            timeout_in_sec, self.POLL_INTERVAL) if timeout_in_sec != 0 else self.POLL_INTERVAL
        while True:
            chk_sfp = sfp_event.check_all_port_interrupt_event()
            int_sfp = sfp_event.update_port_event_object(
                chk_sfp, int_sfp) if chk_sfp else int_sfp

            current_milli_time = int(round(time.time() * 1000))
            if int_sfp or (timeout != 0 and current_milli_time - start_milli_time > timeout):
                self._init_cmis_module(int_sfp, cmis_init_script)
                break

            time.sleep(sleep_time)

        return True, int_sfp

    def get_qsfp_data(self, eeprom_ifraw):
        sfp_data = {}
        sfpi_obj = sff8436InterfaceId(eeprom_ifraw)
        sfpd_obj = sff8436Dom(eeprom_ifraw) if sfpi_obj else {}

        sfp_data['interface'] = sfpi_obj.get_data_pretty() if sfpi_obj else {}
        sfp_data['dom'] = sfpd_obj.get_data_pretty() if sfpd_obj else {}
        return sfp_data

    def get_eeprom_dict(self, port_num):
        """Returns dictionary of interface and dom data.
        format: {<port_num> : {'interface': {'version' : '1.0', 'data' : {...}},
                               'dom' : {'version' : '1.0', 'data' : {...}}}}
        """

        sfp_data = {}

        eeprom_ifraw = self.get_eeprom_raw(port_num)
        eeprom_domraw = self.get_eeprom_dom_raw(port_num)

        if eeprom_ifraw is None:
            return None

        if port_num in self.osfp_ports:
            sfpi_obj = inf8628InterfaceId(eeprom_ifraw)
            if sfpi_obj:
                sfp_data['interface'] = sfpi_obj.get_data_pretty()

                # check if it is a 100G module
                if sfp_data['interface']['data']['Identifier'] not in [type_of_transceiver['18'], type_of_transceiver['19']]:
                    return self.get_qsfp_data(eeprom_ifraw)

            sfpd_obj = QSFPDDDomPaser(
                eeprom_ifraw + eeprom_domraw) if eeprom_domraw else None
            sfp_data['dom'] = sfpd_obj.get_data_pretty() if sfpd_obj else {}

            return sfp_data
        else:
            sfpi_obj = sff8472InterfaceId(eeprom_ifraw)
            if sfpi_obj is not None:
                sfp_data['interface'] = sfpi_obj.get_data_pretty()
                cal_type = sfpi_obj.get_calibration_type()

            if eeprom_domraw is not None:
                sfpd_obj = sff8472Dom(eeprom_domraw, cal_type)
                if sfpd_obj is not None:
                    sfp_data['dom'] = sfpd_obj.get_data_pretty()

            return sfp_data
        return

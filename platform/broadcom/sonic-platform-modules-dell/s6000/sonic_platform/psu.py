#!/usr/bin/env python

########################################################################
# DellEMC S6000
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSUs' information which are available in the platform
#
########################################################################


try:
    import os
    from sonic_platform_base.psu_base import PsuBase
    from sonic_platform.eeprom import Eeprom
    from sonic_platform.fan import Fan
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")


class Psu(PsuBase):
    """DellEMC Platform-specific PSU class"""

    CPLD_DIR = "/sys/devices/platform/dell-s6000-cpld.0/"
    I2C_DIR = "/sys/class/i2c-adapter/"

    def __init__(self, psu_index):
        # PSU is 1-based in DellEMC platforms
        self.index = psu_index + 1
        self.psu_presence_reg = "psu{}_prs".format(psu_index)
        self.psu_status_reg = "powersupply_status"

        if self.index == 1:
            ltc_dir = self.I2C_DIR + "i2c-11/11-0042/hwmon/"
        else:
            ltc_dir = self.I2C_DIR + "i2c-11/11-0040/hwmon/"
        hwmon_node = os.listdir(ltc_dir)[0]
        self.HWMON_DIR = ltc_dir + hwmon_node + '/'

        self.psu_voltage_reg = self.HWMON_DIR + "in1_input"
        self.psu_current_reg = self.HWMON_DIR + "curr1_input"
        self.psu_power_reg = self.HWMON_DIR + "power1_input"

        self.eeprom = Eeprom(is_psu=True, psu_index=self.index)

        # Overriding _fan_list class variable defined in PsuBase, to
        # make it unique per Psu object
        self._fan_list = []

        self._fan_list.append(Fan(self.index, psu_fan=True, dependency=self))

    def _get_cpld_register(self, reg_name):
        # On successful read, returns the value read from given
        # reg_name and on failure returns 'ERR'
        rv = 'ERR'
        cpld_reg_file = self.CPLD_DIR + reg_name

        if (not os.path.isfile(cpld_reg_file)):
            return rv

        try:
            with open(cpld_reg_file, 'r') as fd:
                rv = fd.read()
        except:
            rv = 'ERR'

        rv = rv.rstrip('\r\n')
        rv = rv.lstrip(" ")
        return rv

    def _get_i2c_register(self, reg_file):
        # On successful read, returns the value read from given
        # reg_name and on failure returns 'ERR'
        rv = 'ERR'

        if (not os.path.isfile(reg_file)):
            return rv

        try:
            with open(reg_file, 'r') as fd:
                rv = fd.read()
        except:
            rv = 'ERR'

        rv = rv.rstrip('\r\n')
        rv = rv.lstrip(" ")
        return rv

    def get_name(self):
        """
        Retrieves the name of the device

        Returns:
            string: The name of the device
        """
        return "PSU{}".format(self.index)

    def get_presence(self):
        """
        Retrieves the presence of the Power Supply Unit (PSU)

        Returns:
            bool: True if PSU is present, False if not
        """
        status = False
        psu_presence = self._get_cpld_register(self.psu_presence_reg)
        if (psu_presence != 'ERR'):
            psu_presence = int(psu_presence)
            if psu_presence:
                status = True

        return status

    def get_model(self):
        """
        Retrieves the part number of the PSU

        Returns:
            string: Part number of PSU
        """
        return self.eeprom.part_number_str()

    def get_serial(self):
        """
        Retrieves the serial number of the PSU

        Returns:
            string: Serial number of PSU
        """
        # Sample Serial number format "US-01234D-54321-25A-0123-A00"
        return self.eeprom.serial_number_str()

    def get_status(self):
        """
        Retrieves the operational status of the PSU

        Returns:
            bool: True if PSU is operating properly, False if not
        """
        status = False
        psu_status = self._get_cpld_register(self.psu_status_reg)
        if (psu_status != 'ERR'):
            psu_status = (int(psu_status, 16) >> ((2 - self.index) * 4)) & 0xF
            if (~psu_status & 0b1000) and (~psu_status & 0b0100):
                status = True

        return status

    def get_voltage(self):
        """
        Retrieves current PSU voltage output

        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        psu_voltage = self._get_i2c_register(self.psu_voltage_reg)
        if (psu_voltage != 'ERR') and self.get_status():
            # Converting the value returned by driver which is in
            # millivolts to volts
            psu_voltage = float(psu_voltage) / 1000
        else:
            psu_voltage = 0.0

        return psu_voltage

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU

        Returns:
            A float number, electric current in amperes,
            e.g. 15.4
        """
        psu_current = self._get_i2c_register(self.psu_current_reg)
        if (psu_current != 'ERR') and self.get_status():
            # Converting the value returned by driver which is in
            # milliamperes to amperes
            psu_current = float(psu_current) / 1000
        else:
            psu_current = 0.0

        return psu_current

    def get_power(self):
        """
        Retrieves current energy supplied by PSU

        Returns:
            A float number, the power in watts,
            e.g. 302.6
        """
        psu_power = self._get_i2c_register(self.psu_power_reg)
        if (psu_power != 'ERR') and self.get_status():
            # Converting the value returned by driver which is in
            # microwatts to watts
            psu_power = float(psu_power) / 1000000
        else:
            psu_power = 0.0

        return psu_power

    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU
        Returns:
            A boolean, True if PSU has stablized its output voltages and
            passed all its internal self-tests, False if not.
        """
        status = False
        psu_status = self._get_cpld_register(self.psu_status_reg)
        if (psu_status != 'ERR'):
            psu_status = (int(psu_status, 16) >> ((2 - self.index) * 4)) & 0xF
            if (psu_status == 0x2):
                status = True

        return status

    def get_status_led(self):
        """
        Gets the state of the PSU status LED

        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings.
        """
        if self.get_powergood_status():
            return self.STATUS_LED_COLOR_GREEN
        else:
            return self.STATUS_LED_COLOR_OFF

    def set_status_led(self, color):
        """
        Sets the state of the PSU status LED
        Args:
            color: A string representing the color with which to set the
                   PSU status LED
        Returns:
            bool: True if status LED state is set successfully, False if
                  not
        """
        # In S6000, the firmware running in the PSU controls the LED
        # and the PSU LED state cannot be changed from CPU.
        return False

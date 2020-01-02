#!/usr/bin/env python

#############################################################################
# DellEmc S6100
#
# Platform and model specific eeprom subclass, inherits from the base class,
# and provides the followings:
# - the eeprom format definition
# - specific encoder/decoder if there is special need
#############################################################################

try:
    from sonic_eeprom import eeprom_tlvinfo
    import binascii
except ImportError, e:
    raise ImportError (str(e) + "- required module not found")


class Eeprom(eeprom_tlvinfo.TlvInfoDecoder):

    def __init__(self, i2c_line=0, iom_eeprom=False):
        self.is_module = iom_eeprom
        if self.is_module:
            self.eeprom_path = ("/sys/class/i2c-adapter"
                                "/i2c-{0}/{0}-0050/eeprom").format(i2c_line)
        else:
            self.eeprom_path = "/sys/class/i2c-adapter/i2c-2/2-0050/eeprom"
        super(Eeprom, self).__init__(self.eeprom_path, 0, '', True)
        self.eeprom_tlv_dict = dict()

        try:
            if self.is_module:
                self.write_eeprom("\x00\x00")
                self.eeprom_data = self.read_eeprom_bytes(256)
            else:
                self.eeprom_data = self.read_eeprom()
        except:
            self.eeprom_data = "N/A"
            if not self.is_module:
                raise RuntimeError("Eeprom is not Programmed")
        else:
            eeprom = self.eeprom_data

            if not self.is_valid_tlvinfo_header(eeprom):
                return

            total_length = (ord(eeprom[9]) << 8) | ord(eeprom[10])
            tlv_index = self._TLV_INFO_HDR_LEN
            tlv_end = self._TLV_INFO_HDR_LEN + total_length

            while (tlv_index + 2) < len(eeprom) and tlv_index < tlv_end:
                if not self.is_valid_tlv(eeprom[tlv_index:]):
                    break

                tlv = eeprom[tlv_index:tlv_index + 2
                             + ord(eeprom[tlv_index + 1])]
                code = "0x%02X" % (ord(tlv[0]))

                if ord(tlv[0]) == self._TLV_CODE_VENDOR_EXT:
                    value = str((ord(tlv[2]) << 24) | (ord(tlv[3]) << 16) |
                                (ord(tlv[4]) << 8) | ord(tlv[5]))
                    value += str(tlv[6:6 + ord(tlv[1])])
                else:
                    name, value = self.decoder(None, tlv)

                self.eeprom_tlv_dict[code] = value
                if ord(eeprom[tlv_index]) == self._TLV_CODE_CRC_32:
                    break

                tlv_index += ord(eeprom[tlv_index+1]) + 2


    def serial_number_str(self):
        (is_valid, results) = self.get_tlv_field(
                    self.eeprom_data, self._TLV_CODE_SERIAL_NUMBER)
        if not is_valid:
            return "N/A"

        return results[2]

    def base_mac_addr(self):
        (is_valid, results) = self.get_tlv_field(
                    self.eeprom_data, self._TLV_CODE_MAC_BASE)
        if not is_valid or results[1] != 6:
            return super(TlvInfoDecoder, self).switchaddrstr(e)

        return ":".join([binascii.b2a_hex(T) for T in results[2]])

    def modelstr(self):
        if self.is_module:
            (is_valid, results) = self.get_tlv_field(
                        self.eeprom_data, self._TLV_CODE_PLATFORM_NAME)
        else:
            (is_valid, results) = self.get_tlv_field(
                        self.eeprom_data, self._TLV_CODE_PRODUCT_NAME)
        if not is_valid:
            return "N/A"

        return results[2]

    def part_number_str(self):
        (is_valid, results) = self.get_tlv_field(
                    self.eeprom_data, self._TLV_CODE_PART_NUMBER)
        if not is_valid:
            return "N/A"

        return results[2]

    def serial_str(self):
        (is_valid, results) = self.get_tlv_field(
                    self.eeprom_data, self._TLV_CODE_SERVICE_TAG)
        if not is_valid:
            return "N/A"

        return results[2]

    def revision_str(self):
        (is_valid, results) = self.get_tlv_field(
                    self.eeprom_data, self._TLV_CODE_DEVICE_VERSION)
        if not is_valid:
            return "N/A"

        return results[2]

    def system_eeprom_info(self):
        """
        Returns a dictionary, where keys are the type code defined in
        ONIE EEPROM format and values are their corresponding values
        found in the system EEPROM.
        """
        return self.eeprom_tlv_dict

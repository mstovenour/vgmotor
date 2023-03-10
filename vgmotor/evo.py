"""Modbus Package for Regal Beloit EPC VGreen Motor family

VGMotorEVO provides access to the EVO specific configuration storage

WARNING:  Config addresses are all unique to VGreen EVO motor.  
          Similar config exists for other motors but at different 
          flash address locations.
"""

from . generic import VGMotorGeneric
from . evoschedule import EVOSchedule

class VGMotorEVO(VGMotorGeneric):
    """Provides access to the EVO specific configuration storage

    Only known working configuration is included.  See the evo_config_dump
    file for more possibilities.
    
    """

    _PAGE = 0
    _ADDRESS = 1
    _LEN = 2
    _FORMAT = 3
    _ERROR = 4

    #                      (page, addr, len, str_fmt,     err_txt)
    SERIAL_TIMEOUT =       (0x01, 0x00,   1, '{}s',       '~~')
    MOTOR_ADDRESS =        (0x01, 0x01,   1, '0x{:02x}',  '~~~~')
    DIGITAL_INPUT_ENABLE = (0x0a, 0x57,   1, '{}',        '~')
    DIGITAL_INPUT_RPM =    (0x0a, 0x58,   2, '{:>4} RPM', '~~~~ RPM')
    SELECTED_SCHEDULE_A =  (0x0b, 0x00,   1, '{}',        '~')
    SELECTED_SCHEDULE_B =  (0x0c, 0x00,   1, '{}',        '~')
    START_SCHEDULE_A =     (0x0b, 0x08,   1, None,        None)
    START_SCHEDULE_B =     (0x0c, 0x08,   1, None,        None)


    def serial_timeout(self, unit, **kwargs):
        """Read or Write serial control timeout

        The number of seconds the LVM will wait after receiving the last
        serial command before resuming the built in schedule.  This is a
        watch dog failsafe if a serial controller stops polling.

        If called with the timeout named argument, writes that value to the
        config memory. Always returns the current value of the timeout
        setting.

        :param unit:  Target Modbus slave address
        :param timeout: (optional) new timeout seconds
        :returns: timeout seconds as int or formatted string
        """
        if kwargs.get('timeout'):
            ret_val = kwargs['timeout']
            #TODO: write the timeout to flash
        else:
            ret_val = self._read_config_tuple(unit, VGMotorEVO.SERIAL_TIMEOUT)
        return ret_val

    def motor_address(self, unit, **kwargs):
        """Read or Write motor slave address

        If called with the address named argument, writes that value to the
        config memory. Always returns the current value of the address
        setting.

        :param unit:  Target Modbus slave address
        :param address: (optional) new motor slave address
        :returns: motor slave address as int or formatted string
        """
        if kwargs.get('address'):
            ret_val = kwargs['address']
            #TODO: write the address to flash
        else:
            ret_val = self._read_config_tuple(unit, VGMotorEVO.MOTOR_ADDRESS)
        return ret_val

    def digital_in_enable(self, unit, input, **kwargs):
        """Read or Write enable for digital input

        If called with the enable named argument, writes that value to the
        config memory. Always returns the current value of the enable
        setting.

        :param unit:  Target Modbus slave address
        :param input:  Input number (1-4)
        :param enable: (optional) True|False - Enable value
        :returns: enable value (0|1) as int or formatted string
        """
        if kwargs.get('enable'):
            ret_val = kwargs['enable']
            #TODO: write the enable to flash
        else:
            ret_val = self._read_config_tuple(
                    unit, VGMotorEVO.DIGITAL_INPUT_ENABLE,
                    address_offset=((input-1)*3)
                    )
        return ret_val

    def digital_in_rpm(self, unit, input, **kwargs):
        """Read or Write rpm for digital input

        If called with the rpm named argument, writes that value to the
        config memory. Always returns the current value of the rpm
        setting.

        :param unit:  Target Modbus slave address
        :param input:  Input number (1-4)
        :param rpm: (optional) new RPM value (600-3450)
        :returns: RPM value as int or formatted string
        """
        if kwargs.get('rpm'):
            data = kwargs['rpm']
            ret_val = self._write_config_tuple(
                    unit, VGMotorEVO.DIGITAL_INPUT_RPM, data,
                    address_offset = ((input-1)*3)
                    )
        else:
            ret_val = self._read_config_tuple(
                    unit, VGMotorEVO.DIGITAL_INPUT_RPM,
                    address_offset=((input-1)*3)
                    )
        return ret_val

    def selected_schedule(self, unit, set, **kwargs):
        """Read or Write the selected schedule slot for set

        If called with the slot named argument, writes that value to the
        config memory. Always returns the current value of the schedule
        slot setting.

        :param unit:  Target Modbus slave address
        :param set:  Schedule Set 'A' or 'B'
        :param slot: (named/optional) new schedule slot value (1-8)
        :returns: scheule value as int
        """
        if set == 'A':
            config_tuple = VGMotorEVO.SELECTED_SCHEDULE_A
        else:
            config_tuple = VGMotorEVO.SELECTED_SCHEDULE_B

        if kwargs.get('slot'):
            ret_val = kwargs['slot']
            #TODO: write the schedule slot to flash
        else:
            ret_val = self._read_config_tuple(unit, config_tuple)
        return ret_val

    def _write_config_tuple(self, unit, config_tuple, value, address_offset=0):
        """Writes a config item returning a formatted string representation

        :param unit:  Target Modbus slave address
        :param config_tuple:  Tuple defining the item to read and format
        :param value: integer value to write
        :param address_offset: (optional) Value to add to address to index items
        :returns: _ConfigInt object (int or formatted string)
        """
        length = config_tuple[VGMotorEVO._LEN]
        data = value.to_bytes(length=length, byteorder="little", signed=False)
        val_bytes = self.write_config(
                unit = unit,
                page = config_tuple[VGMotorEVO._PAGE],
                address = config_tuple[VGMotorEVO._ADDRESS] + address_offset,
                length = length,
                data = data
                )
        if val_bytes is not None:
            ret_val = int.from_bytes(val_bytes, "little")
        else:
            ret_val = None

        str_fmt = config_tuple[VGMotorEVO._FORMAT]
        err_txt = config_tuple[VGMotorEVO._ERROR]
        return self._ConfigInt(ret_val, str_fmt, err_txt)

    def _read_config_tuple(self, unit, config_tuple, address_offset=0):
        """Reads a config item returning a formatted string representation

        :param unit:  Target Modbus slave address
        :param config_tuple:  Tuple defining the item to read and format
        :param address_offset: (optional) Value to add to address to index items
        :returns: _ConfigInt object (int or formatted string)
        """
        val_bytes = self.read_config(
                unit = unit,
                page = config_tuple[VGMotorEVO._PAGE],
                address = config_tuple[VGMotorEVO._ADDRESS] + address_offset,
                length = config_tuple[VGMotorEVO._LEN]
                )
        if val_bytes is not None:
            ret_val = int.from_bytes(val_bytes, "little")
        else:
            ret_val = None

        str_fmt = config_tuple[VGMotorEVO._FORMAT]
        err_txt = config_tuple[VGMotorEVO._ERROR]
        return self._ConfigInt(ret_val, str_fmt, err_txt)

    class _ConfigInt(int):
        """Provides both int and string representation of the config

        In string context returns string formatted with str_fmt
        If sensor == none (i.e. bad modbus read) returns err_txt in
        string context and 0 in int context.
        """
        def __new__(cls, value, str_fmt, err_txt):
            if value is None:
                instance = int.__new__(cls, int(0))
            else:
                instance = int.__new__(cls, int(value))
            return instance

        def __init__(self, value, str_fmt, err_txt):
            self._str_fmt = str_fmt
            if value is None:
                self._err_txt = err_txt
            else:
                self._err_txt = None

        def __str__(self):
            if self._err_txt is not None:
                ret_val = self._err_txt
            else:
                #Make sure format is not called in "str" context (recursive loop)
                val = int(self)
                ret_val = self._str_fmt.format(val)
            return ret_val

    def schedule_slot(self, unit:int, set:str, slot:int) -> EVOSchedule:
        """Read a schedule slot
        
        :param unit:  Target Modbus slave address
        :param set:  Schedule set 'A' or 'B'
        :param slot:  Schedule slot 1-8
        :returns: EVOSchedule object holding all steps
        """
        schedule = EVOSchedule( set, slot)
        if set == 'A':
            config_tuple = VGMotorEVO.START_SCHEDULE_A
        else:
            config_tuple = VGMotorEVO.START_SCHEDULE_B
        page = config_tuple[VGMotorEVO._PAGE]
        address = schedule.address(config_tuple[VGMotorEVO._ADDRESS])
        length = schedule.length()

        val_bytes = self.read_config( unit, page, address, length)

        schedule.bytes_to_schedule( val_bytes)

        return schedule

    def schedule_slot_write(self, unit:int, schedule:EVOSchedule) -> EVOSchedule:
        """Write a schedule slot
        
        :param unit:  Target Modbus slave address
        :param schedule:  EVOSchedule object holding all steps
        :returns:  EVOSchedule object holding all steps
        """
        if schedule.set() == 'A':
            config_tuple = VGMotorEVO.START_SCHEDULE_A
        else:
            config_tuple = VGMotorEVO.START_SCHEDULE_B
        page = config_tuple[VGMotorEVO._PAGE]
        address = schedule.address(config_tuple[VGMotorEVO._ADDRESS])
        length = schedule.length()

        data = schedule.schedule_to_bytes()
        val_bytes = self.write_config(
                unit = unit,
                page = page,
                address = address,
                length = length,
                data = data
                )

        schedule.bytes_to_schedule( val_bytes)

        return schedule


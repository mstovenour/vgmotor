"""Modbus Package for Regal Beloit EPC VGreen Motor family

VGMotorGeneric provides formatted responses for each supported sensor and 
item of identification.

"""
from . base import VGMotorBase

class VGMotorGeneric(VGMotorBase):
    """Provides formatted responses for all supported sensor and
    identification common to all motors
    
    """

    _PAGE = 0
    _ADDRESS = 1
    _SCALE = 2
    _FORMAT = 3
    _ERROR = 4

    #                      (page, addr, scale, str_fmt,         err_txt)
    SPEED =                 (0x00, 0x00,    4, '{:4.0f} RPM',   '~~~~ RPM')
    CURRENT =               (0X00, 0X01, 1000, '{:5.2f}A',      '~~.~~A')
    OPERATING_MODE =        (0X00, 0X02, None, '{:d}',          '')
    DEMAND_RPM =            (0x00, 0x03,    4, '{:4.0f} RPM',   '~~~~ RPM')
    DEMAND_TORQUE =         (0x00, 0x03, 1200, '{:5.2f} ft-lb', '~~.~~ ft-lb')
    TORQUE =                (0x00, 0x04, 1200, '{:5.2f} ft-lb', '~~.~~ ft-lb')
    POWER_INVERTER_INPUT =  (0x00, 0x05, None, '{:4.0f}W',      '~~~~W')
    TEMP_AMBIENT =          (0x00, 0x07,  128, '{:5.1f}C',      '~~.~C')
    POWER_SHAFT_OUTPUT =    (0x00, 0x0a, None, '{:4.0f}W',      '~~~~W')
    #VOLTAGE_1 =            (0X00, 0X0d, None, '{:3.0f}V',      '~~~V') #???
    #POWER_MOTOR_INPUT =    (0X00, 0X11, None, '{:2.0f}W',      '~~~~W') #???
    DIGITAL_INPUT_ACTIVE =  (0x00, 0x14, None, '0b{:08b}',      '0b~~~~~~~~')
    #VOLTAGE_2 =            (0x01, 0x1f, None, '{:3.0f}V',      '~~~V') #???
    #VOLTAGE_3 =            (0x03, 0x02, None, '{:3.0f}V',      '~~~V') #???
    #DIGITAL_INPUT_STATUS = (0X03, 0X09, None, '0b{:08b}',      '0b~~~~~~~~') #???


    def read_sensor(self, unit, sensor):
        """Return a formatted representation of a sensor
        
        :param unit:  Target Modbus slave address
        :param sensor: VGMotorGeneric tuple for requested sensor
        :returns: float which evaluates to a formatted string
        """
        page = sensor[VGMotorGeneric._PAGE]
        address = sensor[VGMotorGeneric._ADDRESS]
        scale = sensor[VGMotorGeneric._SCALE]
        str_fmt = sensor[VGMotorGeneric._FORMAT]
        err_txt = sensor[VGMotorGeneric._ERROR]

        value = super().read_sensor(unit, page, address)
        if value is not None:
            if value != 0 and scale is not None:
                value = value / scale
        return(self._MotorSensor(value, str_fmt, err_txt))

    class _MotorSensor(float):
        """Provides both float and string representation of the sensor

        In string context returns string formatted with str_fmt
        If sensor == none (i.e. bad modbus read) returns err_txt in
        string context and NaN in float context.
        """
        def __new__(cls, value, str_fmt, err_txt):
            if value is None:
                instance = float.__new__(cls, float("NaN"))
            else:
                instance = float.__new__(cls, float(value))
            return instance

        def __init__(self, value, str_fmt, err_txt):
            self._str_fmt = str_fmt
            self._err_txt = err_txt

        def __str__(self):

            if self != self:  #is NaN?
                ret_val = self._err_txt
            else:
                try:
                    #Make sure format is not called in "str" context (recursive loop)
                    val = float(self)
                    ret_val = self._str_fmt.format(val)
                except ValueError:
                    val = int(self)
                    ret_val = self._str_fmt.format(val)
            return ret_val

    def read_identification(self, unit):
        """Reads and parses the motor identification data
        
        Return a class with methods for each element
        
        :param unit:  Target Modbus slave address
        :returns: MotorIdentification class
        """

        data = self.read_id(unit, address=0x00, length=27)
        return(self.MotorIdentification(data))

    class MotorIdentification():
        """Class holding motor identification with methods for each element

        Parses the raw byte string into each formatted element
        """

        def __init__(self, data):
            self._drive_sw = "~~.~~.~~"
            self._lvb_sw = "~~.~~"
            self._product_id = "~~~~"
            self._drive_hp = "~~.~~"
            if data is not None:
                txt = data.decode(encoding='utf-8')
                self._drive_sw = f"{txt[0x03]}{txt[0x02]}.{txt[0x01]}{txt[0x00]}.{txt[0x15]}{txt[0x16]}"
                self._lvb_sw = f"{txt[0x17]}{txt[0x18]}.{txt[0x19]}{txt[0x1a]}"
                self._product_id = f"0x{data[0x04]:02x}"
                self._drive_hp = f"{float(f'{txt[0x13]}{txt[0x12]}.{txt[0x11]}{txt[0x10]}'):.2f} HP"

        def drive_sw(self):
            return self._drive_sw
        def lvb_sw(self):
            return self._lvb_sw
        def product_id(self):
            return self._product_id
        def drive_hp(self):
            return self._drive_hp

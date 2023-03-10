"""Modbus Package for Regal Beloit EPC VGreen Motor family

VGMotorBase implements all of the supported custom Modbus commands.

These motors do not implement any of the standard Modbus commands.  The
basic RTU Frame is standard as is the physial RS-485 interface.  The
commands they do implement are structured differently from standard Modbus
commands.
NOTE:  All words are passed little endian on the wire
       All functions include extra ACK byte (0x20 - request / 0x10 - response)
       Multi-byte reads use a length-1 parameter that is different from
       standard Modbus functions

This class only implements the client side of the request / response message
classes.  See
https://github.com/riptideio/pymodbus/tree/dev/examples/v2.5.3/custom_message.py
for examples of the server methods if this is ever extended to provide a
server implemenation.
"""
from pymodbus.pdu import ModbusRequest, ModbusResponse, ExceptionResponse
import pymodbus.client.base
import pymodbus.exceptions as exceptions
import struct
import logging

log = logging.getLogger()

class VGMotorBase:
    """Base class for the VGreen motor family

    This class is intended to be subclassed by a spcific motor 
    implementation, however it can be used directly for raw access
    to sensors and configuration addresses.
    """
    def __init__(self, client):
        """Registers each response message with the decoder

        :param client: a ModbusBaseClient object
        """
        if not isinstance(client, pymodbus.client.base.ModbusBaseClient):
            raise exceptions.ParameterException("client must be a ModbusBaseClient class")
        self.client = client

        self.client.register(GoResponse)
        self.client.register(StopResponse)
        self.client.register(StatusResponse)
        self.client.register(SetDemandResponse)
        self.client.register(ReadSensorResponse)
        self.client.register(ReadIDResponse)
        self.client.register(ReadConfigResponse)
        self.client.register(WriteConfigResponse)
        self.client.register(StoreConfigResponse)

    def go(self, unit):
        """Performs Modbus Go Function (0x41)

        Errors are logged. Returns true if no errors.

        :param unit:  Target Modbus slave address
        :returns: True - no errors
        """
        request = GoRequest(unit=unit)
        values = self._execute_modbus_function(request)
        return values

    def stop(self, unit):
        """Performs Modbus Stop Function (0x42)

        Errors are logged. Returns true if no errors.

        :param unit:  Target Modbus slave address
        :returns: True - no errors
        """
        request = StopRequest(unit=unit)
        values = self._execute_modbus_function(request)
        return values

    def status(self, unit):
        """Performs Modbus Status Function (0x43)

        Errors are logged. Returns MotorStatus() if no errors, None on 
        error. MotorStatus evaluates to an int except when calling 
        __str__ (e.g. print()) where it will evaluate to a text 
        representation of the status.

        :param unit:  Target Modbus slave address
        :returns: status value or None on error
        """
        request = StatusRequest(unit=unit)
        values = self._execute_modbus_function(request)
        if values is not None:
            return MotorStatus(values[0])

        return values

    def set_demand(self, unit, mode, demand):
        """Performs Modbus Set Demand Function (0x44)

        Errors are logged. Returns true if no errors.  Setting a demand
        value will take precedence over any built in schedule.  The LVM
        will enter a watchdog mode where this demand value will remain
        active so long as the serial interface continues to send commands
        of some kind (e.g. status) at an interval less than the serial 
        timeout setting (default: 60s).

        :param unit:  Target Modbus slave address
        :param mode:  0-Speed, 1-Torque
        :param demand:  Requested speed(RPM) or torque(lb-ft)
        :returns: True - no errors
        """
        request = SetDemandRequest(unit=unit, mode=mode, demand=demand)
        values = self._execute_modbus_function(request)
        if values is not None:
            if mode == 0:
                return int(values[0] / 4)  #RPM
            else:
                return int(values[0] / 1200)  #Torque

        return values

    def read_sensor(self, unit, page, address):
        """Performs Modbus Read Sensor Function (0x45)

        Errors are logged and None is returned, otherwise a single 
        value is retured.

        :param unit:  Target Modbus slave address
        :param page:  Sensor page
        :param address:  Sensor address on page
        :returns: Sensor value or None on error
        """
        request = ReadSensorRequest(unit=unit, page=page, address=address)
        values = self._execute_modbus_function(request)
        if values is not None:
            return values[0]

        return values

    def read_id(self, unit, address, length):
        """Performs Modbus Read Identification Function (0x46)

        Errors are logged. Returns bytes as read

        :param unit:  Target Modbus slave address
        :param address:  Identity address to read
        :param length:  Number of bytes to read
        :returns: bytearray of read bytes; None on error
        """
        request = ReadIDRequest(unit=unit, address=address, length=length)
        values = self._execute_modbus_function(request)
        return values

    def read_config(self, unit, page, address, length):
        """Performs Modbus Read Configuration Function (0x64)

        Errors are logged. Returns bytes as read

        :param unit:  Target Modbus slave address
        :param page:  Config page to read
        :param address:  Config address to read
        :param length:  Number of bytes to read
        :returns: bytearray of read bytes; None on error
        """
        request = ReadConfigRequest(unit=unit, page=page, address=address, length=length)
        values = self._execute_modbus_function(request)
        return values

    def write_config(self, unit, page, address, length, data):
        """Performs Modbus Write Configuration Function (0x64)

        Errors are logged. Returns bytes as read

        :param unit:  Target Modbus slave address
        :param page:  Config page to read
        :param address:  Config address to read
        :param length:  Number of bytes to read
        :param data: bytearray of data to write
        :returns: bytearray of read bytes; None on error
        """
        request = WriteConfigRequest(unit=unit, page=page, address=address, length=length, data=data)
        values = self._execute_modbus_function(request)
        return values

    def store_config(self, unit):
        """Performs Modbus Store Config Function (0x65)

        Errors are logged. Returns true if no errors.

        :param unit:  Target Modbus slave address
        :returns: True - no errors
        """
        request = StoreConfigRequest(unit=unit)
        values = self._execute_modbus_function(request)
        return values

    def _execute_modbus_function(self, request):
        """Calls Modbus library execute() and logs errors

        :param request: ModbusRequest class to execute
        :returns: None - Errors; True - success; or values[] for data


        GoResponse:  sets values == None or True
            return values
        StopResponse: sets values == None or True
            return values
        StatusResponse: sets values == None or [] w/ one value
            return values[0]
        SetDemandResponse: sets values == None or [] w/ one value
            return int(values[0] / scale)
        ReadSensorResponse: sets values == None or [] w/ one value
            return values[0]
        ReadIDResponse: sets values == None or [] variable length
            return values
        ReadConfigResponse: sets values == None or [] variable length
            return values
        WriteConfigResponse: sets values == None or [] variable length
            return values
        StoreConfigResponse: sets values == None or True
            return values

        result.values is set per three cases:
            None or True
            None or [] w/ one value
            None or [] w/ variable length

        """
        result = self.client.execute(request)
        values = None
        if isinstance(result, exceptions.ModbusException):
            log.error(result)
        elif isinstance(result, ExceptionResponse):
            #result.values with be None
            log.error(f"Modbus slave 0x{result.unit_id:02x} responded with an error: "
                      f"function: 0x{result.original_code:02x}, "
                      f"Modbus exception: 0x{result.exception_code:02x}")
        else:
            values = result.values
        
        return values


class GoRequest(ModbusRequest):
    """(0x41) Go Modbus request class"""

    function_code = 0x41
    # Unit:1 + Function:1 + ACK:1 + CRC:2
    _rtu_frame_size = 1+1+1+2 #5

    def __init__(self, unit, **kwargs):
        """Instantiate Request PDU
        
        :param unit:  Target Modbus slave address
        """
        super().__init__(unit, **kwargs)

    def encode(self):
        """Encode function envelope

        This device message has an extra, mandatory ACK byte (0x20)
        """
        return struct.pack("<B", 0x20)

    def get_response_pdu_size(self):
        """Returns response pdu size"""
        #framework adds 3 (unit and CRC)
        return self._rtu_frame_size - 3

class GoResponse(ModbusResponse):
    """(0x41) Go Modbus response"""

    function_code = 0x41
    #This determines the number of bytes read for this response frame.
    _rtu_frame_size = 5  #entire response frame

    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.ack = None
        self.values = None

    def decode(self, data):
        """Decode Read Sensor response function envelope

        This device message has an extra, mandatory ACK byte (0x10).

        :param data: The byte stream to decode
        """
        self.ack = struct.unpack("<B", data)
        self.values = True


class StopRequest(ModbusRequest):
    """(0x42) Stop Modbus request class"""

    function_code = 0x42
    # Unit:1 + Function:1 + ACK:1 + CRC:2
    _rtu_frame_size = 1+1+1+2 #5

    def __init__(self, unit, **kwargs):
        """Instantiate Request PDU
        
        :param unit:  Target Modbus slave address
        """
        super().__init__(unit, **kwargs)

    def encode(self):
        """Encode function envelope

        This device message has an extra, mandatory ACK byte (0x20)
        """
        return struct.pack("<B", 0x20)

    def get_response_pdu_size(self):
        """Returns response pdu size"""
        #framework adds 3 (unit and CRC)
        return self._rtu_frame_size - 3

class StopResponse(ModbusResponse):
    """(0x42) Stop Modbus response"""

    function_code = 0x42
    #This determines the number of bytes read for this response frame.
    _rtu_frame_size = 5  #entire response frame

    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.ack = None
        self.values = None

    def decode(self, data):
        """Decode Read Sensor response function envelope

        This device message has an extra, mandatory ACK byte (0x10).

        :param data: The byte stream to decode
        """
        self.ack = struct.unpack("<B", data)
        self.values = True


class StatusRequest(ModbusRequest):
    """(0x43) Status Modbus request class"""

    function_code = 0x43
    # Unit:1 + Function:1 + ACK:1 + status:1 + CRC:2
    _rtu_frame_size = 1+1+1+1+2 #6

    def __init__(self, unit, **kwargs):
        """Instantiate Request PDU

        :param unit:  Target Modbus slave address
        """
        super().__init__(unit, **kwargs)

    def encode(self):
        """Encode function envelope

        This device message has an extra, mandatory ACK byte (0x20)
        """
        return struct.pack("<B", 0x20)

    def get_response_pdu_size(self):
        """Returns response pdu size"""
        #framework adds 3 (unit and CRC)
        return self._rtu_frame_size - 3

class StatusResponse(ModbusResponse):
    """(0x43) Status Modbus response"""

    function_code = 0x43
    #This determines the number of bytes read for this response frame.
    _rtu_frame_size = 6  #entire response frame

    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.ack = None
        self.values = None

    def decode(self, data):
        """Decode Read Sensor response function envelope

        This device message has an extra, mandatory ACK byte (0x10).

        :param data: The byte stream to decode
        """
        self.values = []
        self.ack, value = struct.unpack("<BB", data)
        self.values.append(value)


class MotorStatus(int):
    """Provides both int and string representation of motor status

    If status == None (i.e. bad modbus read) returns error text in
    string context and zero in int context.
    """
    MODE_STOP = 0x00 # stop mode – motor stopped
    MODE_RUN_BOOT = 0x09 # run mode – boot (motor is getting ready to spin)
    MODE_RUN_VECTOR = 0x0b # run mode – vector
    MODE_FAULT = 0x20 # fault mode – motor stopped

    MODE = {
        MODE_STOP : "STOP",
        MODE_RUN_BOOT : "RUN BOOT",
        MODE_RUN_VECTOR : "RUN",
        MODE_FAULT : "FAULT",
    }

    def __new__(cls, value):
        if value is None:
            instance = int.__new__(cls, int(0))
        else:
            instance = int.__new__(cls, int(value))
        return instance

    def __init__(self, value, error_txt="Modbus Error"):
        if value is None:
            self.error_txt = error_txt
        else:
            self.error_txt = None

    def __str__(self):
        if self.error_txt is not None:
            return self.error_txt
        elif self in MotorStatus.MODE.keys():
            return MotorStatus.MODE[self]
        else:
            return f'0x{self:02x}'


class SetDemandRequest(ModbusRequest):
    """(0x44) Set Demand Modbus request class

    Speed demand value is 4x the requested RPM
    Torque demand value is 1200x the requested ft-lb
    """

    function_code = 0x44
    # Unit:1 + Function:1 + ACK:1 + mode:1 + demand:2 + CRC:2
    _rtu_frame_size = 1+1+1+1+2+2 #8

    def __init__(self, unit, mode, demand, **kwargs):
        """Instantiate Request PDU

        :param unit:  Target Modbus slave address
        :param mode:  0-Speed, 1-Torque
        :param demand:  Requested speed(RPM) or torque(lb-ft)
        """
        super().__init__(unit, **kwargs)
        self.mode = mode
        self.demand = demand

    def encode(self):
        """Encode function envelope

        This device message has an extra, mandatory ACK byte (0x20)
        """
        if self.mode == 0:
            demand = self.demand * 4  #Multiply RPM by 4
        else:
            demand = self.demand * 1200 #Multiply Torque by 1200
        return struct.pack("<BBH", 0x20, self.mode, demand)

    def get_response_pdu_size(self):
        """Returns response pdu size"""
        #framework adds 3 (unit and CRC)
        return self._rtu_frame_size - 3

class SetDemandResponse(ModbusResponse):
    """(0x44) Set Demand Modbus response"""

    function_code = 0x44
    #This determines the number of bytes read for this response frame.
    _rtu_frame_size = 8  #entire response frame

    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.ack = None
        self.values = None

    def decode(self, data):
        """Decode Read Sensor response function envelope

        This device message has an extra, mandatory ACK byte (0x10).

        :param data: The byte stream to decode
        """
        self.values = []
        self.ack, self.mode, value = struct.unpack("<BBH", data)
        self.values.append(value)


class ReadSensorRequest(ModbusRequest):
    """(0x45) Read Sensor Modbus request class

    Sensor pages and addresses are common across the VGreen family but 
    each motor faimly has different set of supported sensors.
    """

    function_code = 0x45
    # Unit:1 + Function:1 + ACK:1 + Page:1 + Address:1 + value:2 + CRC:2
    _rtu_frame_size = 1+1+1+1+1+2+2 #9

    def __init__(self, unit, page, address, **kwargs):
        """Instantiate Request PDU

        :param unit:  Target Modbus slave address
        :param page:  Sensor page
        :param address:  Sensor address on page
        """
        super().__init__(unit, **kwargs)
        self.page = page
        self.address = address

    def encode(self):
        """Encode function envelope

        This device message has an extra, mandatory ACK byte (0x20)
        """
        return struct.pack("<BBB", 0x20, self.page, self.address)

    def get_response_pdu_size(self):
        """Returns response pdu size"""
        #framework adds 3 (unit and CRC)
        return self._rtu_frame_size - 3

class ReadSensorResponse(ModbusResponse):
    """(0x45) Read Sensor Modbus response

    Sensor pages and addresses are common across the VGreen family but 
    each motor faimly has different set of supported sensors.
    """

    function_code = 0x45
    #This determines the number of bytes read for this response frame.
    _rtu_frame_size = 9  #entire response frame

    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.ack = None
        self.page = None
        self.address = None
        self.values = None

    def decode(self, data):
        """Decode Read Sensor response function envelope

        This device message has an extra, mandatory ACK byte (0x10).

        :param data: The byte stream to decode
        """
        self.values = []
        self.ack, self.page, self.address, value = struct.unpack("<BBBH", data)
        self.values.append(value)


class ReadIDRequest(ModbusRequest):
    """(0x46) Read Identification Modbus request class

    On the wire, length is one less than the requested length.
    e.g. 0 will request one byte.  The library uses length as 
    the real length in all operations.  The adjustment is made 
    just before encoding to the wire and just after decoding 
    from the wire.
    """

    function_code = 0x46
    # Unit:1 + Function:1 + ACK:1 + page:1 + address:1 +length:1 + CRC:2
    _rtu_frame_size = 1+1+1+1+1+1+2 #8

    def __init__(self, unit, address, length, **kwargs):
        """Instantiate Request PDU
        
        :param unit:  Target Modbus slave address
        :param address:  Identity address to read
        :param length:  Number of bytes to read
        """
        super().__init__(unit, **kwargs)
        self.page = 0x00  #There is only one page (0x00) for Identification
        self.address = address
        self.length = length

    def encode(self):
        """Encode function envelope

        This device message has an extra, mandatory ACK byte (0x20)
        """
        length = self.length-1
        return struct.pack("<BBBB", 0x20, self.page, self.address, length)

    def get_response_pdu_size(self):
        """Returns response pdu size"""
        #framework adds 3 (unit and CRC)
        return self._rtu_frame_size - 3 + self.length

class ReadIDResponse(ModbusResponse):
    """(0x46) Read Identification Modbus response"""

    function_code = 0x46
    _rtu_byte_count_pos = 5  #Used to index the length parameter in response

    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.ack = None
        self.page = None
        self.address = None
        self.length = None
        self.values = None

    def decode(self, data):
        """Decode Read Sensor response function envelope

        This device message has an extra, mandatory ACK byte (0x10).
        
        :param data: The byte stream to decode
        """
        self.ack, self.page, self.address, length = struct.unpack("<BBBB", data[:4])
        self.length = length + 1
        self.values = data[4:]

    @classmethod
    def calculateRtuFrameSize(cls, buffer):  # pylint: disable=invalid-name
        """Calculate the size of a PDU.

        On the wire, length is one less than the requested length. 
        e.g. 0 will request one byte.  This requires a custom implemenation 
        for calculateRtuFrameSize() as no standard Modbus functions operate 
        this way.

        :param buffer: A buffer containing the data that have been received.
        :returns: The number of bytes in the PDU.
        :raises NotImplementedException:
        """
        return int(buffer[cls._rtu_byte_count_pos])+1 + cls._rtu_byte_count_pos + 3


class ReadConfigRequest(ModbusRequest):
    """(0x64) Read Config Modbus request class
    
    On the wire, length is one less than the requested length.
    e.g. 0 will request one byte.  The library uses length as 
    the real length in all operations.  The adjustment is made 
    just before encoding to the wire and just after decoding 
    from the wire.
    """

    function_code = 0x64
    # Unit:1 + Function:1 + ACK:1 + page:1 + address:1 +length:1 + CRC:2
    _rtu_frame_size = 1+1+1+1+1+1+2 #8

    def __init__(self, unit, page, address, length, **kwargs):
        """Instantiate Request PDU

        :param unit:  Target Modbus slave address
        :param page:  Config page to read
        :param address:  config address to read
        :param length:  Number of bytes to read
        """
        super().__init__(unit, **kwargs)
        self.page = page
        self.address = address
        self.length = length

    def encode(self):
        """Encode function envelope

        This device message has an extra, mandatory ACK byte (0x20)
        """
        length = self.length-1
        return struct.pack("<BBBB", 0x20, self.page, self.address, length)

    def get_response_pdu_size(self):
        """Returns response pdu size"""
        #framework adds 3 (unit and CRC)
        return self._rtu_frame_size - 3 + self.length

class ReadConfigResponse(ModbusResponse):
    """(0x64) Read Config Modbus response"""

    function_code = 0x64
    _rtu_byte_count_pos = 5  #Used to index the length parameter in response

    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.ack = None
        self.page = None
        self.address = None
        self.length = None
        self.values = None

    def decode(self, data):
        """Decode Read Sensor response function envelope

        This device message has an extra, mandatory ACK byte (0x10).

        :param data: The byte stream to decode
        """
        self.ack, self.page, self.address, length = struct.unpack("<BBBB", data[:4])
        self.length = length + 1
        self.values = data[4:]

    @classmethod
    def calculateRtuFrameSize(cls, buffer):  # pylint: disable=invalid-name
        """Calculate the size of a PDU.

        On the wire, length is one less than the requested length. 
        e.g. 0 will request one byte.  This requires a custom implemenation 
        for calculateRtuFrameSize() as no standard Modbus functions operate 
        this way.

        :param buffer: A buffer containing the data that have been received.
        :returns: The number of bytes in the PDU.
        :raises NotImplementedException:
        """
        return int(buffer[cls._rtu_byte_count_pos])+1 + cls._rtu_byte_count_pos + 3

class WriteConfigRequest(ModbusRequest):
    """(0x64) Write Config Modbus request class

    On the wire, length is one less than the requested length.
    e.g. 0 will request one byte.  The library uses length as 
    the real length in all operations.  The adjustment is made 
    just before encoding to the wire and just after decoding 
    from the wire.

    Read and write use the same modbus command code.  A write 
    operation is signified by setting the MSB of the page parameter.
    """

    function_code = 0x64
    # Unit:1 + Function:1 + ACK:1 + page:1 + address:1 +length:1 + CRC:2
    _rtu_frame_size = 1+1+1+1+1+1+2 #8

    def __init__(self, unit, page, address, length, data, **kwargs):
        """Instantiate Request PDU
        
        :param unit:  Target Modbus slave address
        :param page:  Config page to read
        :param address:  config address to read
        :param length:  Number of bytes to read
        :param data: bytearray of data to write
        """
        super().__init__(unit, **kwargs)
        self.page = page
        self.address = address
        self.length = length
        self.data = data

    def encode(self):
        """Encode function envelope

        This device message has an extra, mandatory ACK byte (0x20)

        Writing is the same as reading with the MSB of the page byte set.
        """
        length = self.length-1
        #Indicate write by setting the MSB of the page byte
        self.page |= 0x80
        header = struct.pack("<BBBB", 0x20, self.page, self.address, length)
        return header + self.data

    def get_response_pdu_size(self):
        """Returns response pdu size"""
        #framework adds 3 (unit and CRC)
        return self._rtu_frame_size - 3 + self.length

class WriteConfigResponse(ModbusResponse):
    """(0x64) Write Config Modbus response"""

    function_code = 0x64
    _rtu_byte_count_pos = 5  #Used to index the length parameter in response

    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.ack = None
        self.page = None
        self.address = None
        self.length = None
        self.values = None

    def decode(self, data):
        """Decode Read Sensor response function envelope

        This device message has an extra, mandatory ACK byte (0x10).
        
        :param data: The byte stream to decode
        """
        self.ack, self.page, self.address, length = struct.unpack("<BBBB", data[:4])
        self.length = length + 1
        self.values = data[4:]

    @classmethod
    def calculateRtuFrameSize(cls, buffer):  # pylint: disable=invalid-name
        """Calculate the size of a PDU.

        On the wire, length is one less than the requested length. 
        e.g. 0 will request one byte.  This requires a custom implemenation 
        for calculateRtuFrameSize() as no standard Modbus functions operate 
        this way.

        :param buffer: A buffer containing the data that have been received.
        :returns: The number of bytes in the PDU.
        :raises NotImplementedException:
        """
        return int(buffer[cls._rtu_byte_count_pos])+1 + cls._rtu_byte_count_pos + 3

class StoreConfigRequest(ModbusRequest):
    """(0x65) Go Modbus request class"""

    function_code = 0x65
    # Unit:1 + Function:1 + ACK:1 + CRC:2
    _rtu_frame_size = 1+1+1+2 #5

    def __init__(self, unit, **kwargs):
        """Instantiate Request PDU
        
        :param unit:  Target Modbus slave address
        """
        super().__init__(unit, **kwargs)

    def encode(self):
        """Encode function envelope

        This device message has an extra, mandatory ACK byte (0x20)
        """
        return struct.pack("<B", 0x20)

    def get_response_pdu_size(self):
        """Returns response pdu size"""
        #framework adds 3 (unit and CRC)
        return self._rtu_frame_size - 3

class StoreConfigResponse(ModbusResponse):
    """(0x65) Store Config Modbus response"""

    function_code = 0x65
    #This determines the number of bytes read for this response frame.
    _rtu_frame_size = 5  #entire response frame

    def __init__(self, **kwargs):
        super().__init__( **kwargs)
        self.ack = None
        self.values = None

    def decode(self, data):
        """Decode Read Sensor response function envelope

        This device message has an extra, mandatory ACK byte (0x10).

        :param data: The byte stream to decode
        """
        self.ack = struct.unpack("<B", data)
        self.values = True


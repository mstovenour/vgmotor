#!/usr/bin/env python3
"""Pymodbus Synchronous Client for Regal Beloit EPC

This is a test client implementing each of the base functions.  The base
functions can be useful when studying a new motor series and developing a
subclass unique to the motor series.

This test client specifically focuses on config write functions
"""
import logging, time, sys

from pymodbus.client import ModbusSerialClient as ModbusClient
from vgmotor import VGMotorBase

from pymodbus import pymodbus_apply_logging_config
pymodbus_apply_logging_config()  #Default level: WARNING
log = logging.getLogger()
# log.setLevel(logging.DEBUG)
# log.setLevel(logging.CRITICAL)

port = "/dev/ttyUSB0"


def main(motor):

    unit = 0x15

    print(f"Read some Configuration data")

    # WARNING:  Config addresses are all unique to VGreen EVO motor.  
    #           Similar config exists for other motors but at different 
    #           flash address locations.

    def to_str_little(val_bytes, val_fmt, val_none):
        """"""
        if val_bytes is not None:
            val_int = int.from_bytes(val_bytes, "little")
            return val_fmt.format(val_int)
        else:
            return val_none

    # 0x0a:0x58 : 7a0d   (IN1 3450 RPM)
    val_bytes = motor.read_config(unit=unit, page=0x0a, address=0x58, length=2)
    print(f"\tIN1 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0a:0x5b : 5f05   (IN2 1375 RPM)
    val_bytes = motor.read_config(unit=unit, page=0x0a, address=0x5b, length=2)
    print(f"\tIN2 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0a:0x5e : 280a   (IN3 2600 RPM)
    val_bytes = motor.read_config(unit=unit, page=0x0a, address=0x5e, length=2)
    print(f"\tIN3 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0a:0x61 : d606   (IN4 1750 RPM)
    val_bytes = motor.read_config(unit=unit, page=0x0a, address=0x61, length=2)
    print(f"\tIN4 RPM:", to_str_little(val_bytes, "{}", "~~~~"))

    # 0x0b:0x00 : 05    (currently selected A set schedule)
    val_bytes = motor.read_config(unit=unit, page=0x0b, address=0x00, length=1)
    print(f"\tSchedule Set A Selected Schedule:", to_str_little(val_bytes, "{}", "~"))
    # 0x0b:0x3e : 18    (Schedule A:5 duration = 24h)
    val_bytes = motor.read_config(unit=unit, page=0x0b, address=0x3e, length=1)
    print(f"\tSchedule Set A / Schedule 5 Hours:", to_str_little(val_bytes, "{}", "~~"))
    # 0x0b:0x3f : bd06  (Schedule A:5 RPM = 3450)
    val_bytes = motor.read_config(unit=unit, page=0x0b, address=0x3f, length=2)
    print(f"\tSchedule Set A / Schedule 5 RPM:", to_str_little(val_bytes, "{}", "~~"))


    print(f"Change some Configuration data")
    # 0x0a:0x58 : 7a0d   (IN1 3450 RPM)
    data = (2200).to_bytes(length=2, byteorder="little", signed=False)
    val_bytes = motor.write_config(unit=unit, page=0x0a, address=0x58, length=2, data=data)
    print(f"\tIN1 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0a:0x5b : 5f05   (IN2 1375 RPM)
    data = (2600).to_bytes(length=2, byteorder="little", signed=False)
    val_bytes = motor.write_config(unit=unit, page=0x0a, address=0x5b, length=2, data=data)
    print(f"\tIN2 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0a:0x5e : 280a   (IN3 2600 RPM)
    data = (3450).to_bytes(length=2, byteorder="little", signed=False)
    val_bytes = motor.write_config(unit=unit, page=0x0a, address=0x5e, length=2, data=data)
    print(f"\tIN3 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0b:0x3f : bd06  (Schedule A:5 RPM = 3450)
    data = (1500).to_bytes(length=2, byteorder="little", signed=False)
    val_bytes = motor.write_config(unit=unit, page=0x0b, address=0x3f, length=2, data=data)
    print(f"\tSchedule Set A / Schedule 5 RPM:", to_str_little(val_bytes, "{}", "~~"))


    print(f"Verify changes to Flash Configuration data")
    # 0x0a:0x58 : 7a0d   (IN1 3450 RPM)
    val_bytes = motor.read_config(unit=unit, page=0x0a, address=0x58, length=2)
    print(f"\tIN1 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0a:0x5b : 5f05   (IN2 1375 RPM)
    val_bytes = motor.read_config(unit=unit, page=0x0a, address=0x5b, length=2)
    print(f"\tIN2 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0a:0x5e : 280a   (IN3 2600 RPM)
    val_bytes = motor.read_config(unit=unit, page=0x0a, address=0x5e, length=2)
    print(f"\tIN3 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0a:0x61 : d606   (IN4 1750 RPM)
    val_bytes = motor.read_config(unit=unit, page=0x0a, address=0x61, length=2)
    print(f"\tIN4 RPM:", to_str_little(val_bytes, "{}", "~~~~"))
    # 0x0b:0x3f : bd06  (Schedule A:5 RPM = 3450)
    val_bytes = motor.read_config(unit=unit, page=0x0b, address=0x3f, length=2)
    print(f"\tSchedule Set A / Schedule 5 RPM:", to_str_little(val_bytes, "{}", "~~"))


if __name__ == "__main__":
    print(f'Connecting to the Modbus Network at {port}')
    with ModbusClient( method='rtu', port=port, baudrate=9600, bytesize=8,
                parity='N', stopbits=1, timeout=1 ) as client:

        vgmotor = VGMotorBase(client)

        time.sleep(1)
        try:
            main(vgmotor)
        except KeyboardInterrupt:
            sys.exit(2)

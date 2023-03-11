#!/usr/bin/env python3
"""Pymodbus Synchronous Client for Regal Beloit EPC

This is a test client implementing each of the base functions.  The base
functions can be useful when studying a new motor series and developing a
subclass unique to the motor series.

This test client specifically focuses on config and sensor read functions
"""
import logging, time, sys

from pymodbus.client import ModbusSerialClient as ModbusClient
from vgmotor import VGMotorBase

from pymodbus import pymodbus_apply_logging_config
pymodbus_apply_logging_config(logging.WARNING)  #Default level: DEBUG
log = logging.getLogger()
# log.setLevel(logging.DEBUG)
# log.setLevel(logging.CRITICAL)

port = "/dev/ttyUSB0"


def main(motor):

    unit = 0x15

    print(f"Read some Identification data")
    data = motor.read_id(unit, 0x00, 0x1b)
    if data is None:
        drive_sw = "~~.~~.~~"
        lvb_sw = "~~.~~"
        product_id = "~~~~"
        drive_hp = "~~.~~"
    else:
        txt = data.decode(encoding='utf-8')
        drive_sw = f"{txt[0x03]}{txt[0x02]}.{txt[0x01]}{txt[0x00]}.{txt[0x15]}{txt[0x16]}"
        lvb_sw = f"{txt[0x17]}{txt[0x18]}.{txt[0x19]}{txt[0x1a]}"
        product_id = f"0x{data[0x04]:02x}"
        drive_hp = f"{float(f'{txt[0x13]}{txt[0x12]}.{txt[0x11]}{txt[0x10]}'):.2f}"

    print(f"\tDrive Software Version: {drive_sw}")
    print(f"\tLVB Software Version: {lvb_sw}")
    print(f"\tProduct ID: {product_id}")
    print(f"\tHorsepower: {drive_hp} HP")


    print(f"Read some VGreen EVO Configuration data (invalid on other motors)")

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

    # 0x01:0x00 (Serial Timeout = 60s)
    val_bytes = motor.read_config(unit=unit, page=0x01, address=0x00, length=1)
    print(f"\tSerial Timeout:", to_str_little(val_bytes, "{}s", "~~"))

    # 0x01:0x01 (Motor Address = 0x15)
    val_bytes = motor.read_config(unit=unit, page=0x01, address=0x01, length=1)
    print(f"\tMotor Address:", to_str_little(val_bytes, "0x{:02x}", "~~~~"))

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


    print('\nRead a few sensors (ctl-c to quit)')
    while (True):
        rpm_demand = motor.read_sensor(unit, 0x00, 0x03)
        rpm_demand = rpm_demand/4 if rpm_demand is not None else float("nan")
        rpm = motor.read_sensor(unit, 0x00, 0x00)
        rpm = rpm/4 if rpm is not None else float("nan")
        temp = motor.read_sensor(unit, 0x00, 0x07)
        temp = temp/128 if temp is not None else float("nan")
        torque = motor.read_sensor(unit, 0x00, 0x04)
        torque = torque if torque is not None else float("nan")
        power = motor.read_sensor(unit, 0x00, 0x05)
        power = power if power is not None else float("nan")
        input_bytes = motor.read_sensor(unit, 0x00, 0x14)
        input = f"0b{input_bytes:08b}" if input_bytes is not None else "~~~~~~~~~~"

        print(f"\t{rpm_demand=:.0f} {rpm=:.0f} {temp=:.0f} {torque=:.0f} {power=:.0f} {input=:}")
        time.sleep(0.50)


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

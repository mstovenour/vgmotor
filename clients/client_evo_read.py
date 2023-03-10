#!/usr/bin/env python3
"""Pymodbus Synchronous Client for Regal Beloit Century VGreen EVO Motor

This is a test client implementing some of the EVO functions.

This test client specifically focuses on config and status read functions.
"""
import logging, time, sys

from pymodbus.client import ModbusSerialClient as ModbusClient
from vgmotor import VGMotorEVO

from pymodbus import pymodbus_apply_logging_config
pymodbus_apply_logging_config(logging.WARNING)  #Default level: DEBUG
log = logging.getLogger()
# log.setLevel(logging.DEBUG)
# log.setLevel(logging.CRITICAL)

port = "/dev/ttyUSB0"


def main(motor:VGMotorEVO):

    unit = 0x15

    print(f"Read some Identification data")
    identification = motor.read_identification(unit)
    print(f"\tDrive Software Version:", identification.drive_sw())
    print(f"\tLVB Software Version:", identification.lvb_sw())
    print(f"\tProduct ID:", identification.product_id())
    print(f"\tHorsepower:", identification.drive_hp())

    print(f"\nRead some Configuration data")
    print(f"\tSerial Timeout:", motor.serial_timeout(unit))
    print(f"\tMotor Address:", motor.motor_address(unit))
    print(f"\tDigital Inputs")
    print(f"\tInput Enable  RPM")
    for index in range(1,4+1):
        print("\t    {:1d} {}   {}".format(
                index,
                bool(motor.digital_in_enable(unit, index)),
                str(motor.digital_in_rpm(unit, index))
                ))

    print(f"\tSchedule Set A")
    print(f"\tSelected Schedule:", motor.selected_schedule(unit, 'A'))
    print("\tSlot Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM ")
    for index in range(1,8+1):
        print("\t  ", index, motor.schedule_slot(unit, 'A', index))

    print(f"\tSchedule Set B")
    print(f"\tSelected Schedule:", motor.selected_schedule(unit, 'B'))
    print("\tSlot Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM ")
    for index in range(1,8+1):
        print("\t  ", index, motor.schedule_slot(unit, 'B', index))
    
    print('\nRead a few sensors (ctl-c to quit)')
    lines = 100
    while (True):
        demand = motor.read_sensor(unit, VGMotorEVO.DEMAND_RPM)
        speed = motor.read_sensor(unit, VGMotorEVO.SPEED)
        temp = motor.read_sensor(unit, VGMotorEVO.TEMP_AMBIENT)
        torque = motor.read_sensor(unit, VGMotorEVO.TORQUE)
        power_inverter = motor.read_sensor(unit, VGMotorEVO.POWER_INVERTER_INPUT)
        power_shaft = motor.read_sensor(unit, VGMotorEVO.POWER_SHAFT_OUTPUT)
        current = motor.read_sensor(unit, VGMotorEVO.CURRENT)
        di_active = motor.read_sensor(unit, VGMotorEVO.DIGITAL_INPUT_ACTIVE)
        mode = motor.read_sensor(unit, VGMotorEVO.OPERATING_MODE)

        if lines > 10:
            if lines != 100:
                print(f"\n")
            lines = 0
            print(f"\tDemand    Speed     Temp    Torque      Inverter Shaft Current  Input      Mode")
        print(f"\t{demand}  {speed}  {temp}  {torque}  {power_inverter}   {power_shaft} {current}   {di_active} {mode}")
        lines += 1
        time.sleep(0.50)


if __name__ == "__main__":
    print(f'Connecting to the Modbus Network at {port}')
    with ModbusClient( method='rtu', port=port, baudrate=9600, bytesize=8,
                parity='N', stopbits=1, timeout=1 ) as client:

        vgmotor = VGMotorEVO(client)

        time.sleep(1)
        try:
            main(vgmotor)
        except KeyboardInterrupt:
            sys.exit(2)

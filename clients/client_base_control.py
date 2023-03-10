#!/usr/bin/env python3
"""Pymodbus Synchronous Client for Regal Beloit EPC

This is a test client implementing each of the base functions.  The base
functions can be useful when studying a new motor series and developing a
subclass unique to the motor series.

This test client specifically focuses on motor control functions
"""
import logging, time, sys, random

from pymodbus.client import ModbusSerialClient as ModbusClient
from vgmotor.base import VGMotorBase

from pymodbus import pymodbus_apply_logging_config
pymodbus_apply_logging_config()  #Default level: WARNING
log = logging.getLogger()
# log.setLevel(logging.DEBUG)
# log.setLevel(logging.CRITICAL)

port = "/dev/ttyUSB0"


def main(motor):

    unit = 0x15

    print("Performing stop, demand, go, and status functions")
    status = motor.status(unit)
    print(f"\tStatus: {status}")

    print(f"\tStopping motor for 5 seconds", end='')
    print(" --> success" if motor.stop(unit) else " --> failed")

    status = 0xff
    print(f"\tStatus: ", end='')
    while status and status != 0x00:
        status = motor.status(unit)
        print(f"{status} ", end='', flush=True)
        time.sleep(0.50)
    time.sleep(5)

    print(f"\n\tStarting motor", end='')
    print(" --> success" if motor.go(unit) else " --> failed")

    status = 0xff
    print(f"\tStatus: ", end='')
    while status and status != 0x0b:
        status = motor.status(unit)
        print(f"{status} ", end='', flush=True)
        time.sleep(0.50)
    time.sleep(10)

    demand = int((random.randrange(1000,2001)+25/2) / 25) * 25
    print(f"\n\tSetting demand to {demand} RPM", end='')
    print(" --> success" if motor.set_demand(unit, 0, demand) else " --> failed")


    print('Reading a few sensors (ctl-c to quit)')
    while (True):
        rpm_demand = motor.read_sensor(unit, 0x00, 0x03)
        rpm_demand = rpm_demand/4 if rpm_demand is not None else float("nan")
        rpm = motor.read_sensor(unit, 0x00, 0x00)
        rpm = rpm/4 if rpm is not None else float("nan")
        temp = motor.read_sensor(unit, 0x00, 0x07)
        temp = temp/128 if temp is not None else float("nan")
        torque = motor.read_sensor(unit, 0x00, 0x04)
        torque = torque/1200 if torque is not None else float("nan")
        power = motor.read_sensor(unit, 0x00, 0x05)
        power = power if power is not None else float("nan")
        input_bytes = motor.read_sensor(unit, 0x00, 0x14)
        input = f"0b{input_bytes:08b}" if input_bytes is not None else "~~~~~~~~~~"

        print(f"\t{rpm_demand=:.0f} {rpm=:.0f} {temp=:.1f} {torque=:.2f} {power=:.0f} {input=:}")
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

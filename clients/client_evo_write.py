#!/usr/bin/env python3
"""Pymodbus Synchronous Client for Regal Beloit Century VGreen EVO Motor

This is a test client implementing each of the EVO functions.

This test client specifically focuses on config write functions.
"""
import logging, time, sys

from pymodbus.client import ModbusSerialClient as ModbusClient
from vgmotor import VGMotorEVO, EVOSchedule

from pymodbus import pymodbus_apply_logging_config
pymodbus_apply_logging_config(logging.WARNING)  #Default level: DEBUG
log = logging.getLogger()
# log.setLevel(logging.DEBUG)
# log.setLevel(logging.CRITICAL)

port = "/dev/ttyUSB0"


def main(motor:VGMotorEVO):

    unit = 0x15

    print(f"Read some Configuration data")

    print(f"\tDigital Inputs")
    print(f"\tInput Enable  RPM")
    for index in range(1,4+1):
        print("\t    {:1d} {}   {}".format(
                index,
                bool(motor.digital_in_enable(unit,index)),
                str(motor.digital_in_rpm(unit,index))
                ))

    print(f"\tSchedule Set A")
    print(f"\tSelected Schedule:", motor.selected_schedule(unit, 'A'))
    print("\tSlot Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM ")
    for index in range(1,8+1):
        print("\t  ", index, motor.schedule_slot(unit, 'A', index))


    print(f"\nChange some Configuration data")
    # (IN1 default 3450 RPM)
    ret_val = motor.digital_in_rpm(unit, 1, rpm=3450)
    print(f"\tNew IN1 RPM:", ret_val)
    # (IN2 default 1375 RPM)
    ret_val = motor.digital_in_rpm(unit, 2, rpm=1375)
    print(f"\tNew IN2 RPM:", ret_val)
    # (IN3 default 2600 RPM)
    ret_val = motor.digital_in_rpm(unit, 3, rpm=2600)
    print(f"\tNew IN3 RPM:", ret_val)
    # (IN4 default 1750 RPM)
    ret_val = motor.digital_in_rpm(unit, 4, rpm=1750)
    print(f"\tNew IN4 RPM:", ret_val)

    # (Schedule A:5 RPM = 1725)
    schedule = EVOSchedule( 'A', 5)
    schedule.step(1, 24, 1725)
    ret_val = motor.schedule_slot_write(unit, schedule)
    print(f"\tNew Schedule A/5:", ret_val)


    print(f"\nVerify changes to Configuration data")
    print(f"\tDigital Inputs")
    print(f"\tInput Enable  RPM")
    for index in range(1,4+1):
        print("\t    {:1d} {}   {}".format(
                index,
                bool(motor.digital_in_enable(unit,index)),
                str(motor.digital_in_rpm(unit,index))
                ))

    print(f"\tSchedule Set A")
    print(f"\tSelected Schedule:", motor.selected_schedule(unit, 'A'))
    print("\tSlot Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM ")
    for index in range(1,8+1):
        print("\t  ", index, motor.schedule_slot(unit, 'A', index))

    if not query_yes_no("\nSave changes to Flash?"):
        return


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


if __name__ == "__main__":
    print(f'Connecting to the Modbus Network at {port}')
    with ModbusClient( method='rtu', port=port, baudrate=9600, bytesize=8,
                parity='N', stopbits=1, timeout=1 ) as client:

        vgmotor = VGMotorEVO(client)

        time.sleep(1)
        try:
            main(vgmotor)
        except KeyboardInterrupt:
            #sys.exit(2)
            pass

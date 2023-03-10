"""Modbus Package for Regal Beloit EPC VGreen Motor family

These motors do not implement any of the standard Modbus commands.  The 
basic RTU Frame is the same as is the physial RS-485 interface.  The 
commands they do implement are framed differently from standard Modbus 
commands.  This package implements the custom Modbus functions supported 
by these motors.  There are multiple motors in the family and each have 
unique characteristics, especially the configuration flash structure. 
Each unique motor type is implemented in a sub-class.

Supported Modbus Functions
    0x41: go()
    0x42: stop()
    0x43: status()
    0x44: set_demand()
    0x45: read_sensor()
    0x46: read_id()
    0x64: read_config() / write_config()
    0x65: store_config()

The exposed class structure for this package is as follows and each class
inherits from the class above:
    VGMotorBase:  Implements the base Modbus functions above.  Sensor, ID,
                  and Config methods all take raw page/address as input.
    VGMotorGeneric:  Implements read_sensor() and read_id() for all VGreen
                  motor types.  These methods expose named constants for
                  each supported sensor and config item which map to the
                  page, address, data type, and units string.
    VGMotorEVO:   Implements config read/write methods for the VGreen EVO
                  motor.  Each motor has a very different config structure
                  and this class exposes methods specific to the
                  configuration of an EVO motor.

"""
__VERSION__ = '0.1.0'
from vgmotor.evoschedule import EVOSchedule
from vgmotor.base import VGMotorBase, MotorStatus
from vgmotor.generic import VGMotorGeneric
from vgmotor.evo import VGMotorEVO

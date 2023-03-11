*******
vgmotor
*******

Project Description
===================

This is a modbus package for the Regal Beloit EPC VGreen Motor family.
This package implements the custom Modbus functions supported by these
motors.  There are multiple motors in the family and each have unique
characteristics, especially the configuration flash structure. Each
unique motor type is implemented in a sub-class.

These motors do not implement *any* of the standard Modbus commands.  The 
basic RTU Frame is the same as is the physial RS-485 interface.  The 
commands they do implement are framed differently from standard Modbus 
commands.

The VGMotorBase and VGMotorGeneric classes implement read / command methods
that should work with all vgreen motors.  The VGMotorEVO class implements
config read/write methods that will *ONLY* work with the EVO motor.  DO NOT
ATTEMPT TO WRITE THE CONFIG OF OTHER MOTORS WITH THE VGMotorEVO CLASS.  While
the only motor supported in the vgreen family is the EVO, more can be easliy
added.

Supported Modbus Functions
   - 0x41: go()
   -  0x42: stop()
   -  0x43: status()
   -  0x44: set_demand()
   -  0x45: read_sensor()
   -  0x46: read_id()
   -  *0x64: read_config() / write_config()*
   -  0x65: store_config()

NOTE:  0x64 is only supported for the EVO motor and implemented in the 
VGMotorEVO class.

Requirements
============

-  Python 3.9+
-  Linux based system
-  An RS-485 to USB or serial adaptor
-  At least one vgreen motor

Installation
============

You can clone this git repository and install from local sources:

Clone Github Repository
-----------------------

::

   md {some base directory}
   cd {some base directory}
   git clone https://github.com/mstovenour/vgmotor.git vgmotor.git

Create Virtual Environment
--------------------------

Create virtual envrionment in venv and make sure install tools are the
latest version. Ensure that you are using a Python 3 interpreter when
creating the virtual environment.  Your interpreter might be "python" or
"python3".  You can check the version with "python -V" or "python3 -V".
You may also need to change how the virtual environment is invoked
(e.g. the "source" line below), especially on a Windows native python. ::

   cd vgmotor.git
   python3 -m venv venv
   source venv/bin/activate
   python -m pip install --upgrade pip setuptools wheel

Install Package
---------------

This assumes you are in the virtual python 3 environment above::

   python -m pip install -U .

Tryout One of the Clients
-------------------------

This assumes you are in the virtual python 3 environment above::

   python clients/client_evo_read.py

Run Tests
---------

Install Additional Dependencies for Dev and Test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use the -e install if you'd like to develop or test.  It will created
an in place install so that changes to the source are used by your 
installation::

   python -m pip install -e .[test]

Test
^^^^

::

   pytest

or ::

   pytest --cov=vgmotor --cov-report=term-missing --cov-branch

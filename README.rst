*******
vgmotor
*******

Project Description
===================

This is a modbus package for the Century/Regal Beloit EPC VGreen Motor
family. This package implements the custom Modbus functions supported
by these motors.  There are multiple motors in the family and each have
unique characteristics, especially the configuration flash structure.
Each unique motor type should be implemented in a sub-class.

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

Example Clients
===============

There are several example clients in the clients folder. To use this
library you could modify those examples to match your needs. Eventually
this may include a server to create an automation bridge using MQTT or
REST, expecially for polling the motor status.  The clients represent
the descovery process for how to explore a new motor.  Similar exploration
with other motors might take the same path.  The "raw_bytes" client is
useful for studying a completely new motor family.  The "\_base\_*" clients
are useful for extending this package to support other Century/Regal
Beloit EPC based motors.

client_evo_read.py:
  Implements EVO specific functions especially config.
  This client is designed specifically for the VGreen EVO motor.  It will
  read some of the interesting identification and configuration items then
  enter a loop reading the drive status.

::

  (venv) michael@stubby:~/test/vgmotor.git$ python clients/client_evo_read.py
  Connecting to the Modbus Network at /dev/ttyUSB0
  Read some Identification data
          Drive Software Version: 01.20.02
          LVB Software Version: D2.27
          Product ID: 0x1f
          Horsepower: 2.25 HP
  Read some Configuration data
          Serial Timeout: 60s
          Motor Address: 0x15
          Digital Inputs
          Input Enable  RPM
              1 True   3450 RPM
              2 True   1375 RPM
              3 True   2600 RPM
              4 True   1750 RPM
          Schedule Set A
          Selected Schedule: 5
          Slot Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM
             1  2 3450   2 2750   6 1750   2 1150  12    0
             2  2 3450   2 2850   6 1850   2 1250  12    0
             3  4 3450   4 1750   4 1150  12    0
             4  2 3250   8 1150   2 3250  12    0
             5 24 1500   0    0   0    0   0    0
             6 24 1100   0    0   0    0   0    0
             7 24 1725   0    0   0    0   0    0
             8 24 3450   0    0   0    0   0    0
          Schedule Set B
          Selected Schedule: 1
          Slot Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM  Hr  RPM
             1  2 3450   4 2850   4 2250   8 1550   6    0
             2  2 3350   4 2750   4 2150   8 1450   6    0
             3  2 3250   4 2650   4 1950   8 1350   6    0
             4  4 3150   4 2550   4 1850   6 1250   6    0
             5  4 3050   4 2450   4 1750   6 1150   6    0
             6  4 2950   4 2350   4 1650   6 1050   6    0
             7  2 3450   4 2850   4 2250  14 1550  
             8  4 2950   6 2350   8 1650   6 1050  
  Read a few sensors (ctl-c to quit)
          Demand    Speed     Temp    Torque      Inverter Shaft Current  Input      Mode
          1750 RPM  1749 RPM   24.0C   0.69 ft-lb    37W     23W  0.41A   0b00000111 0
          1750 RPM  1749 RPM   24.0C   0.69 ft-lb    37W     23W  0.41A   0b00000111 0
          1750 RPM  1750 RPM   24.0C   0.69 ft-lb    37W     23W  0.41A   0b00000111 0
          1750 RPM  1750 RPM   24.0C   0.69 ft-lb    37W     23W  0.41A   0b00000111 0


client_evo_write.py
  This client is designed specifically for the VGreen EVO motor.  It will
  read some of the configuration items then modify the RPM values for IN1-4
  and Schedule A/5.  Double check that the client_evo_read functions are
  returning sane data before trying to write to your motor.
  DO NOT USE THIS ON NON EVO MOTORS.

client_base_control.py:
  Use generic functions (base class) to control motor.
  The control functions (START, STOP, SET DEMAND, etc.) are common to all
  the motors in the VGreen family.  This client will perform various motor
  commands while outputing the motor status.

::

  (venv) michael@stubby:~/test/vgmotor.git$ python clients/client_base_control.py 
  Connecting to the Modbus Network at /dev/ttyUSB0
  Performing stop, demand, go, and status functions
          Status: STOP
          Stopping motor for 5 seconds --> success
          Status: STOP 
          Starting motor --> success
          Status: RUN 
          Setting demand to 1275 RPM --> success
  Reading a few sensors (ctl-c to quit)
          rpm_demand=1275 rpm=1800 temp=25.0 torque=0.70 power=34 input=0b00000000
          rpm_demand=1275 rpm=1800 temp=25.0 torque=0.50 power=34 input=0b00000000
          rpm_demand=1275 rpm=1260 temp=25.0 torque=0.50 power=34 input=0b00000000
          rpm_demand=1275 rpm=1260 temp=25.0 torque=0.50 power=31 input=0b00000000
          rpm_demand=1275 rpm=1260 temp=25.0 torque=0.50 power=31 input=0b00000000
          rpm_demand=1275 rpm=1275 temp=25.0 torque=0.59 power=31 input=0b00000000
          rpm_demand=1275 rpm=1275 temp=25.0 torque=0.59 power=31 input=0b00000000

client_base_read.py:
   Use generic functions (base class) to read from motor.
   This client exercises read functions that are common to all the VGreen
   motors. The base class is intended to be used by a motor specific class;
   however this client might proove helpful in experimenting with non-EVO
   motors.

client_base_write.py:
   Use generic functions (base class) to write to motor.
   This client exercises write functions that are common to all the VGreen
   motors and exposes generic methods.  The base class is intended to be
   used by a motor specific class; however this client might proove helpful
   in experimenting with non-EVO motors.

client_raw_bytes.py
   This sends and recieves raw unformatted bytes on the modbus network.  This
   can be very handy for discovering how to interact with a new motor.  This
   client program has many commented out pieces of code that were used to
   explore the EVO motor.  Similar techniques could be used to explore 
   different motor types.
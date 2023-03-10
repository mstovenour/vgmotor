"""Pymodbus Synchronous Client for Regal Beloit EPC

This was an early client implementation while studying the VGreen EVO 
motor.  Raw byte strings can be sent to the Modbus client with no library
interpretation.  The raw approach here is useful when blackbox texting
a Modbus client that has implemented custom functions.

Many of the failed tests of various settings are documented below with #xxx-

"""
from pymodbus.client import ModbusSerialClient
from pymodbus.utilities import computeCRC
import time
import struct
import sys

port = "/dev/ttyUSB0"
#port = "/dev/pts/13"
client = ModbusSerialClient(
            method='rtu',
            port=port,
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )

# unit function ack address_h address_l <-- modbus combines two bytes into the address variable
# unit function ack                                   (action)
# unit function ack page      address                 (read 1 data)
# unit function ack page      address   n-1           (read n data)
# unit function ack page      address   n-1 data ...  (write n data)

#go (0x41)        unit  status ack
cmd_go =          [0x15, 0x41, 0x20]
#Stop (0x42)      unit  status ack
cmd_stop =        [0x15, 0x42, 0x20]
#Status (0x43)    unit  status ack
cmd_status_read = [0x15, 0x43, 0x20]
#Demand (0x44)    unit  demand ack   mode  speed speed
cmd_demand_set =  [0x15, 0x44, 0x20, 0x00, 0x90, 0x1a]  #RPM * 4 (0x1a90/4=1700)
cmd_demand_set2 = [0x15, 0x44, 0x20, 0x00, 0x60, 0x09]  #RPM * 4 (0x0960/4=600)
#Write Cfg (0x65) unit  demand ack   mode  speed speed
cmd_write_cfg =   [0x15, 0x65, 0x20]

#RPM (0x45:00:00)     unit sensor ack  page address
sensor_rpm =          [0x15, 0x45, 0x20, 0x00, 0x00]
#demand (0x45:00:03)  unit sensor ack  page address
sensor_demand =       [0x15, 0x45, 0x20, 0x00, 0x03]
#torque (0x45:00:04)  unit sensor ack  page address
sensor_torque =       [0x15, 0x45, 0x20, 0x00, 0x04]
#power (0x45:00:05)   unit sensor ack  page address
sensor_power =        [0x15, 0x45, 0x20, 0x00, 0x05]
#power (0x45:00:11)   unit sensor ack  page address
sensor_power2 =       [0x15, 0x45, 0x20, 0x00, 0x11]
#temp (0x45:00:07)    unit sensor ack  page address
sensor_temp =         [0x15, 0x45, 0x20, 0x00, 0x07]
#voltage (0x45:03:02) unit sensor ack  page address
sensor_voltage =      [0x15, 0x45, 0x20, 0x03, 0x02]
#voltage (0x45:00:0d) unit sensor ack  page address
sensor_voltage2 =     [0x15, 0x45, 0x20, 0x00, 0x0d]

#Read Identification (0x46)

#Configuration Read/Write (0x64) unit   cfg   ack   page  addr  len-1
config_read_protocol           = [0x15, 0x64, 0x20, 0x0a, 0x05, 0x00]
config_write_protocol_jandy    = [0x15, 0x64, 0x20, 0x8a, 0x05, 0x00, 0x01]

#Specific to VGreen EVO
#Configuration Read (0x64)  unit   cfg   ack   page  addr  len-1
config_digital_1_status =   [0x15, 0x64, 0x20, 0x0a, 0x57, 0x00] #unsigned byte
config_digital_1_speed =    [0x15, 0x64, 0x20, 0x0a, 0x58, 0x01] #unsigned int
config_digital_2_status =   [0x15, 0x64, 0x20, 0x0a, 0x5a, 0x00] #unsigned byte
config_digital_2_speed =    [0x15, 0x64, 0x20, 0x0a, 0x5b, 0x01] #unsigned int
config_digital_3_status =   [0x15, 0x64, 0x20, 0x0a, 0x5d, 0x00] #unsigned byte
config_digital_3_speed =    [0x15, 0x64, 0x20, 0x0a, 0x5e, 0x01] #unsigned int
config_digital_4_status =   [0x15, 0x64, 0x20, 0x0a, 0x60, 0x00] #unsigned byte
config_digital_4_speed =    [0x15, 0x64, 0x20, 0x0a, 0x61, 0x01] #unsigned int


#This is in !!Jandy!! format (not modbus)
cmd_jandy_go = [0x10, 0x02, 0x78, 0x41, 0xcb, 0x10, 0x03]


def main():

    #xxx - this indicates that the attempted test did not succeed on an EVO motor
    print("Set Demand to 600 RPM")
    function_raw(cmd_demand_set2)
    print("Issue GO command")
    function_raw(cmd_go)
    # function_raw(config_read_protocol)
    # print(f"Protocol (unsigned byte): {read_config_ub_raw(config_read_protocol)}")
    # print("freeze protection (enabled )")
    # function_raw([0x15, 0x64, 0x20, 0x0a, 0x06, 0x04])
    timeout = read_config_ub_raw([0x15, 0x64, 0x20, 0x01, 0x00, 0x00])
    print(f"Serial Timeout: {timeout}" if timeout is not None else "Serial Timeout: ~~") 
    motor_address = read_config_ub_raw([0x15, 0x64, 0x20, 0x01, 0x01, 0x00])
    print(f"Address: 0x{motor_address:02x}" if motor_address is not None else "Address: ~~~~") 

    # Read schedule set A schedule 5
    # print("Schedule A:5 duration / speed")
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x3e, 0x11])

    # xxx-This changed the value but had no effect on schedule prime speed
    # print("Schedule prime speed")
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x02, 0x01])
    # xxx-print("Write 0xbe0a (2750) to prime speed 0b:02 len 2")
    # function_raw([0x15, 0x64, 0x20, 0x8b, 0x02, 0x01, 0xbe, 0x0a])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x02, 0x01])
    # print("Saving config to NVRAM")
    # function_raw(cmd_write_cfg)

    # !!!! This worked; set Schedule set A / Schedule 5 to to 1500 RPM !!!!
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x3e, 0x11])
    # print("Write 0xdc05 to Schedule set A / Schedule 5 speed 0b:3f len 2")
    # function_raw([0x15, 0x64, 0x20, 0x8b, 0x3f, 0x01, 0xdc, 0x05])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x3e, 0x11])
    # print("Saving config to NVRAM")
    # function_raw(cmd_write_cfg)

    # print(f"System Clock   Hours: {read_sensor_raw([0x15, 0x45, 0x20, 0x03, 0x0a])}")
    # print(f"System Clock Minutes: {read_sensor_raw([0x15, 0x45, 0x20, 0x03, 0x0b])}")
    # print(f"System Clock Seconds: {read_sensor_raw([0x15, 0x45, 0x20, 0x03, 0x0c])}")

    # !!!! This worked; set IN2 to 1500 RPM !!!!
    # function_raw([0x15, 0x64, 0x20, 0x0a, 0x58, 0x07])
    # print("Write 0xdc05 to IN2 speed 0a:5b len 2")
    # function_raw([0x15, 0x64, 0x20, 0x8a, 0x5b, 0x01, 0xdc, 0x05])
    # function_raw([0x15, 0x64, 0x20, 0x0a, 0x58, 0x07])
    # print("Saving config to NVRAM")
    # function_raw(cmd_write_cfg)

    # print("Stopping motor")
    # function_raw(cmd_stop)
    # time.sleep(5)
    # print("Starting motor")
    # function_raw(cmd_demand_set)
    # function_raw(cmd_go)

    # xxx-print("Write 3 to prime duration 0x0a:0x02")
    # xxx-function_raw([0x15, 0x64, 0x20, 0x8a, 0x02, 0x00, 0x03]) #set value but had no effect
    # print("Saving config to NVRAM")
    # function_raw(cmd_write_cfg)

    # print("dump entire config / page 0x00")
    # for x in range(int(16/8)):
    #     begin = int(x*8)
    #     function_raw([0x15, 0x64, 0x20, 0x00, begin, 0x07])
    # function_raw([0x15, 0x64, 0x20, 0x00, 0x10, 0x00])

    # print("dump entire config / page 0x0b")
    # for x in range(int(256/8)):
    #     begin = int(x*8)
    #     function_raw([0x15, 0x64, 0x20, 0x0b, begin, 0x07])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x68, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x69, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x6a, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x6b, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x6c, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x6d, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x6e, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0b, 0x6f, 0x00])

    # print("dump entire config / page 0x0c")
    # for x in range(int(256/8)):
    #     begin = int(x*8)
    #     function_raw([0x15, 0x64, 0x20, 0x0c, begin, 0x07])
    # function_raw([0x15, 0x64, 0x20, 0x0c, 0x78, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0c, 0x79, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0c, 0x7a, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0c, 0x7b, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0c, 0x7c, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0c, 0x7d, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0c, 0x7e, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0c, 0x7f, 0x00])

    #Dump 8 bytes at a time
    # print("dump entire config / page 10 a.k.a. 0x0a")
    # for x in range(int(88/8)):
    #     begin = int(x*8)
    #     function_raw([0x15, 0x64, 0x20, 0x0a, begin, 0x07])
    # function_raw([0x15, 0x64, 0x20, 0x0a, 0x60, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0a, 0x61, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0a, 0x62, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0a, 0x63, 0x00])
    # function_raw([0x15, 0x64, 0x20, 0x0a, 0x64, 0x00])

    # xxx-print(f"Page 02:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x02, 0x00, 0x00])}")
    # xxx-print(f"Page 04:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x04, 0x00, 0x00])}")
    # xxx-print(f"Page 05:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x05, 0x00, 0x00])}")
    # xxx-print(f"Page 06:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x06, 0x00, 0x00])}")
    # xxx-print(f"Page 07:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x07, 0x00, 0x00])}")
    # xxx-print(f"Page 08:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x08, 0x00, 0x00])}")
    # xxx-print(f"Page 09:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x09, 0x00, 0x00])}")
    # xxx-print(f"Page 0d:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x0d, 0x00, 0x00])}")
    # xxx-print(f"Page 0e:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x0e, 0x00, 0x00])}")
    # xxx-print(f"Page 0f:00 (unsigned byte): {read_config_ub_raw([0x15, 0x64, 0x20, 0x0f, 0x00, 0x00])}")


    # xxx-function_raw([0x15, 0x64, 0x20, 0x0a, 0x2d, 0x11])
    # xxx-function_raw([0x15, 0x64, 0x20, 0x0a, 0x23, 0x02])

    # print("schedule type 0-clock / 1-timer")
    # function_raw([0x15, 0x64, 0x20, 0x0a, 0x22, 0x00])
    # xxx-print(f"Step 1 timer rpm (unsigned int): {read_config_ui_raw([0x15, 0x64, 0x20, 0x0a, 0x3c, 0x01])/4}")
    # xxx-print(f"Step 2 timer rpm (unsigned int): {read_config_ui_raw([0x15, 0x64, 0x20, 0x0a, 0x46, 0x01])/4}")
    # xxx-print(f"Step 3 timer rpm (unsigned int): {read_config_ui_raw([0x15, 0x64, 0x20, 0x0a, 0x50, 0x01])/4}")
    # xxx-print(f"Override high timer rpm (unsigned int): {read_config_ui_raw([0x15, 0x64, 0x20, 0x0a, 0x5a, 0x01])/4}")
    # xxx-print(f"Override low timer rpm (unsigned int): {read_config_ui_raw([0x15, 0x64, 0x20, 0x0a, 0x5e, 0x01])/4}")
    # xxx-print(f"Max Speed (unsigned int): {read_config_ui_raw([0x15, 0x64, 0x20, 0x0a, 0x60, 0x01])/4}")

    print(f"digital_1_status: {read_config_ub_raw(config_digital_1_status)}")
    print(f"digital_1_speed: {read_config_ui_raw(config_digital_1_speed)}")
    print(f"digital_2_status: {read_config_ub_raw(config_digital_2_status)}")
    print(f"digital_2_speed: {read_config_ui_raw(config_digital_2_speed)}")
    print(f"digital_3_status: {read_config_ub_raw(config_digital_3_status)}")
    print(f"digital_3_speed: {read_config_ui_raw(config_digital_3_speed)}")
    print(f"digital_4_status: {read_config_ub_raw(config_digital_4_status)}")
    print(f"digital_4_speed: {read_config_ui_raw(config_digital_4_speed)}")


#RPM    Hex   Little Endian
#3450 = 0d7a >> 7a0d
#2750 = 0abe >> be0a
#1750 = 06d6 >> d606
#1150 = 047e >> 7e04

#2850 = 0b22 >> 220b
#1850 = 073a >> 3a07
#1250 = 04e2 >> e204

#3250 = 0cb2 >> b20c
#1725 = 06bd >> bd06
#1100 = 044c >> 4c04

#1375 = 055f >> 5f05
#2600 = 0a28 >> 280a
# 600 = 0258 >> 5802
#1500 = 05dc >> dc05

    print('looping reads (ctl-c to quit)')
    while (True):
        rpm_demand = read_sensor_raw(sensor_demand)
        rpm_demand = rpm_demand/4 if rpm_demand is not None else float("nan")
        rpm = read_sensor_raw(sensor_rpm)
        rpm = rpm/4 if rpm is not None else float("nan")
        temp = read_sensor_raw(sensor_temp)
        temp = temp/128 if temp is not None else float("nan")
        torque = read_sensor_raw(sensor_torque)
        torque = torque/1200 if torque is not None else float("nan")
        power = read_sensor_raw(sensor_power)
        power = power if power is not None else float("nan")
        print(f"{rpm_demand=:.0f} {rpm=:.0f} {temp=:.1f} {torque=:.2f} {power=:.0f}")
        # power2 = read_sensor_raw(sensor_power2)
        # voltage = read_sensor_raw(sensor_voltage)
        # voltage2 = read_sensor_raw(sensor_voltage2)
        # print(f"{rpm_demand=:.0f} {rpm=:.0f} {temp=:.0f} {torque=:.0f} {power=:.0f} {power2=:.0f} {voltage=:.0f} {voltage2=:.0f}")

        time.sleep(0.50)

    # function_raw(cmd_status_read)

    # function_raw(config_read_protocol)
    # #!!!-never tested
    # # function_raw(config_write_protocol_jandy)
    # # function_raw(cmd_config_store)

    # function_raw(cmd_stop)
    # print('sleeping in stopped state')
    # for x in range(4):
    #     rpm_requested = read_sensor_raw(sensor_demand)/4
    #     rpm = read_sensor_raw(sensor_rpm)/4
    #     temp = read_sensor_raw(sensor_temp)
    #     torque = read_sensor_raw(sensor_torque)
    #     power = read_sensor_raw(sensor_power)
    #     print(f"{x=:2.0f} {rpm_requested=:.0f} {rpm=:.0f} {temp=:.0f} {torque=:.2f} {power=:.2f}")
    #     #time.sleep(5)

def function_raw(cmd):
    cmd_crc = bytearray(cmd) + struct.pack(">H", computeCRC(cmd))
    print(f"Send: b'{cmd_crc.hex()}'")
    client.send(cmd_crc)
    response = client.recv(20)
    print(f"Recv: b'{response.hex()}'")

def read_sensor_raw(cmd):
    cmd_crc = bytearray(cmd) + struct.pack(">H", computeCRC(cmd))
    # print(f"Send: b'{cmd_crc.hex()}'")
    client.send(cmd_crc)
    response = client.recv(9)
    time.sleep(0.004)
    # print(f"Recv: b'{response.hex()}'")
    value = None
    if len(response) == 9:
        unit, function, ack, page, address, value, crc = struct.unpack('<BBBBBHH', response)
    elif len(response) == 5:
        unit, function, NACK_code, crc = struct.unpack('<BBBH', response)
        if (function & 0x80):
            print(f"Error: b'{cmd_crc.hex()}' --> Response error: 0x{NACK_code:02x}")
        else:
            print(f"Error: b'{cmd_crc.hex()}' --> Unknown response: 0x{function:02x}:0x{NACK_code:02x}")
    else:
        print(f"Bad Response: b'{response.hex()}'")
    return value

def read_config_ui_raw(cmd):
    """Read Config Register, parse as unsigned int (2 bytes)"""
    cmd_crc = bytearray(cmd) + struct.pack(">H", computeCRC(cmd))
    # print(f"Send: b'{cmd_crc.hex()}'")
    client.send(cmd_crc)
    response = client.recv(10)
    time.sleep(0.004)
    # print(f"Recv: b'{response.hex()}'")
    value = None
    if len(response) == 10:
        unit, function, ack, page, address, length, value, crc = struct.unpack('<BBBBBBHH', response)
    elif len(response) == 5:
        unit, function, NACK_code, crc = struct.unpack('<BBBH', response)
        if (function & 0x80):
            print(f"Error: b'{cmd_crc.hex()}' --> Response error: 0x{NACK_code:02x}")
        else:
            print(f"Error: b'{cmd_crc.hex()}' --> Unknown response: 0x{function:02x}:0x{NACK_code:02x}")
    else:
        print(f"Bad Response: b'{response.hex()}'")
    return value

def read_config_ub_raw(cmd):
    """Read Config Register, parse as unsigned byte"""
    cmd_crc = bytearray(cmd) + struct.pack(">H", computeCRC(cmd))
    # print(f"Send: b'{cmd_crc.hex()}'")
    client.send(cmd_crc)
    response = client.recv(9)
    time.sleep(0.004)
    # print(f"Recv: b'{response.hex()}'")
    value = None
    if len(response) == 9:
        unit, function, ack, page, address, length, value, crc = struct.unpack('<BBBBBBBH', response)
    elif len(response) == 5:
        #Recv:  b'15 e4 03 6b05'
        unit, function, NACK_code, crc = struct.unpack('<BBBH', response)
        if (function & 0x80):
            print(f"Error: b'{cmd_crc.hex()}' --> Response error: 0x{NACK_code:02x}")
        else:
            print(f"Error: b'{cmd_crc.hex()}' --> Unknown response: 0x{function:02x}:0x{NACK_code:02x}")
    else:
        print(f"Bad Response: b'{response.hex()}'")
    return value


if __name__ == "__main__":

    print(f'Tring to connect to the Modbus Network at {port}')
    if not client.connect():  # Trying for connect to Modbus Server/Slave
        print(f'Cannot connect ...')
        sys.exit(1)

    time.sleep(2)
    print('   Connected ...')

    try:
        main()
    except KeyboardInterrupt:
        client.close()
        sys.exit(2)

    client.close()
    sys.exit(0)

"""Modbus Package for Regal Beloit EPC VGreen Motor family

EVOSchedule is a container class for storing and manipualting the EVO schedule

WARNING:  Data structure is likely unique to VGreen EVO motor.
"""

class EVOSchedule:
    """Representation of one schedule slot with either 4 or 5 steps

    The schedule storage was determined empirically and so this may not be
    a complete representation of the configuration.  This logic assumes
    that the schedule configuration is fixed length that the length 
    (i.e. steps) can not be changed.  The factory default schedules have
    either four or five steps each and the durations all add up to 24 hours.

    """

    VALID_STEPS = {
        'A': [0,5,5,4,4,4,4,4,4],
        'B': [0,5,5,5,5,5,5,4,4]
    }
    BYTES_STEP = 3

    def __init__(self, set, slot):
        """Creates empty schedule with correct number of steps
        
        Slots have four or five steps which depend on the set and slot.
        The supported number of steps are hard coded here.

        :param set:  Schedule set 'A' or 'B'
        :param slot:  Schedule slot 1-8 (indexed from 1)
        """
        self._set = set
        self._slot = slot
        self._schedule = self._empty_schedule()

    def __str__(self):
        """
        """
        str_fmt = '{:2d} {:4d}  '
        ret_val = ""
        for slot in self._schedule:
            ret_val += str_fmt.format(slot[0],slot[1])
        
        return ret_val

    def set(self):
        """Returns set

        :returns: set 'A' or 'B'
        """
        return self._set

    def address(self, address_start):
        """Returns address of slot offset from beginning of table

        :param address_start:  Start of schedule set table
        :returns: Address of slot offset
        """
        offset = 0
        for steps in EVOSchedule.VALID_STEPS[self._set][:self._slot]:
            offset += steps * EVOSchedule.BYTES_STEP
        return address_start + offset

    def length(self):
        """Returns total length of schedule slot
        
        :returns: length of schedule slot
        """
        return EVOSchedule.VALID_STEPS[self._set][self._slot] * EVOSchedule.BYTES_STEP

    def step(self, step, duration, speed):
        """Set the duration and speed for a step

        :param step: Step to set (1-4|5; indexed from 1)
        :param duration: Duration in hours (0-24)
        :param speed: Speed in RPM (600-3450)
        """
        self._schedule[step-1] = [duration,speed]

    def bytes_to_schedule(self, val_bytes):
        """Populates schedule slot with data from bytes

        Parses data as schedule structure in little endian ordering. If
        data is None, indicating a Modbus read error, reset the schedule
        to an empty list of slots.
        """
        if val_bytes is None:
            self._schedule = self._empty_schedule()
        else:
            #Loop over the bytes in 3 byte increments storing as steps
            for index in range(int(len(val_bytes)/EVOSchedule.BYTES_STEP)):
                duration_offset = index * EVOSchedule.BYTES_STEP
                duration_byte = val_bytes[duration_offset:duration_offset+1]
                duration = int.from_bytes(duration_byte, 'little')

                speed_offset = (index * EVOSchedule.BYTES_STEP) + 1
                speed_bytes = val_bytes[speed_offset : speed_offset + 2]
                speed = int.from_bytes(speed_bytes, 'little')

                self.step(index + 1, duration, speed)

    def schedule_to_bytes(self):
        """Returns the little endian encoded bytes for a schedule slot

        This will ensure that the steps all add up to 24 hours and
        will pack all the steps with durations pushing zero duration
        steps to the end.
        """
        #Loop over self._schedule array adding up the hours and
        #  recording all non-zero duration steps.
        total_hours = 0
        new_schedule = []
        for step in self._schedule:
            if step[0] > 0:
                total_hours += step[0]
                new_schedule.append(step)
        #If total_hours < 24; put remainder into zero duration step
        if total_hours < 24:
            new_schedule.append([24-total_hours, 0])
        #Pad out remaining steps with zeros
        remainder = EVOSchedule.VALID_STEPS[self._set][self._slot] - len(new_schedule)
        for _ in range(remainder):
            new_schedule.append([0,0])

        #Serialize to little endian bytes
        ret_bytes = bytes()
        for step in new_schedule:
            ret_bytes += int(step[0]).to_bytes(1, 'little')
            ret_bytes += int(step[1]).to_bytes(2, 'little')

        return ret_bytes

    def _empty_schedule(self):
        empty = []
        for _ in range(EVOSchedule.VALID_STEPS[self._set][self._slot]):
            empty.append([0,0])
        return empty

# for circuit python so can communicate via USB


import board
import time
import usb_cdc
import struct
import pwmio

data = []
HEADER = 0xa7
FOOTER = 0x7a
# @dataclass
class Packet:
    # def __init__(cmd, param, len, data, curr_size, complete, all_bytes):
    #     cmd = 
    cmd: int
    param: int
    len: int
    data: list[int]
    curr_size: int
    complete: bool
    all_bytes: bytes
    def __init__(self):
        self.clear()

    def add_byte(self, byte):
        byte &= 0xFF
        if self.curr_size == 0: # header
            if byte != HEADER:
                return False
            self.header = byte
        elif self.curr_size == 1: # cmd
            self.cmd = byte
        elif self.curr_size == 2: # param
            self.param = byte
        elif self.curr_size == 3: # len
            self.len = byte
        elif self.curr_size > 3 and self.curr_size <= 3+self.len: # data
            self.data.append(byte)
            # self.data[self.curr_size-4] = byte
        elif self.curr_size == 4+self.len:
            if byte == FOOTER: # we're done!
                self.all_bytes += bytes([byte])
                self.complete = True
                return True
            else:
                self.clear()
                return False
        else:   #??????
            print("somehow got out of curr_size")
            self.clear()
            return False
        self.all_bytes += bytes([byte])
        self.curr_size += 1
        return True
    
    def to_bytes(self):
        return self.all_bytes
    
    def to_bytes_network(self):
        return self.all_bytes[1:-1]

    def clear(self):
        self.header=self.cmd=self.param=self.len=self.footer=-1
        self.data = []
        self.complete = False
        self.curr_size = 0
        self.all_bytes = []
    
    def is_complete(self):
        return self.complete

read_packet = Packet()

# TODO: determine PWM on boards
pwm_pins = [board.D13, board.D12, board.D24, board.D25, board.SCK, board.MOSI]
pwms = []

def us_to_duty_cycle(us):
    # max value = 1/10 of cycle (20 millisecond, 2 millisecond) = 6553 (0x)
    # mid value = 1/15 of cycle = 4369
    # min value = 1/20 of cycle (20 millisecond, 1 millisecond) = 3277
    return int(us*0xffff/20000)

# COMMANDS
def update_pwm(data):
    # ignore param for now lmao
    if len == 12:
        pwm_vals = struct.unpack(">HHHHHH", data)
        for i in range(6):
            # pwms[i].duty_cycle = us_to_duty_cycle(pwm_vals[i])
            pwms[i].duty_cycle = pwm_vals[i]
            # struct.pack()

def send_hello(Serial):
    Serial.write(bytes([HEADER, 0x00, 0x00, 5, 0x48, 0x45, 'l', 'l', 'o', FOOTER]))  #hello

# FUNNY
def parse_packet(packet):
    if packet.cmd == 0x00:
        send_hello()
    elif packet.cmd == 0x18:
        update_pwm(packet.data)

def main():
    # setup PWM, frequency of 50hz, 
    for i in range(6):
        pwms[i] = pwmio.PWMOut(pwm_pins[i], duty_cycle=4369, frequency=50, variable_frequency=False)

    while True:
        Serial = usb_cdc.enable(console=False, data=True)
        # packet structure: header, cmd, param, 
        if Serial.in_waiting > 0:
            read_packet.add_byte(Serial.read())
            if read_packet.is_complete:
                # parse packet!
                read_packet.clear()

main()
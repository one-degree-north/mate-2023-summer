# for circuit python so can communicate via USB


import board
import time
import usb_cdc
import struct
import pwmio
import adafruit_bno055

# import time

HEADER = 0xa7
FOOTER = 0x7a
# @dataclass


class Packet:
    # def __init__(cmd, param, len, data, curr_size, complete, all_bytes):
    #     cmd = 
    def __init__(self):
        self.cmd = None
        self.param = None
        self.len = None
        self.data = []
        self.curr_size = 0
        self.complete = False
        self.all_bytes = []
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
            # print("somehow got out of curr_size")
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

class rp2040:
    def __init__(self):
        self.read_packet = Packet()
        # TODO: determine PWM on boards
        self.pwm_pins = [board.D13, board.D12, board.D24, board.D25, board.SCK, board.MOSI]
        self.pwms = []
        # Serial = usb_cdc.enable(console=False, data=True)
        self.serial = usb_cdc.console
        i2c = board.I2C()
        self.bno = adafruit_bno055.BNO055_I2C(i2c)

        self.autoreport_delay = 0.9   # seconds
        self.autoreport_clock = 0
        self.autoreport_last_time = time.monotonic()
        self.write_buff = bytes()

    def us_to_duty_cycle(self, us):
        # max value = 1/10 of cycle (20 millisecond, 2 millisecond) = 6553 (0x)
        # mid value = 1/15 of cycle = 4369
        # min value = 1/20 of cycle (20 millisecond, 1 millisecond) = 3277
        return int(us*0xffff/20000)

    # COMMANDS
    def update_pwm(self, data):
        # ignore param for now lmao
        if len(data) == 12:
            pwm_vals = struct.unpack(">HHHHHH", bytes(data))
            for i in range(6):
                # pwms[i].duty_cycle = us_to_duty_cycle(pwm_vals[i])
                self.pwms[i].duty_cycle = pwm_vals[i]

    # def return_thrusters(self):
    #     self.write_buff += bytes([HEADER,])

    def send_hello(self):
        # Serial.write_timeout(bytes([HEADER, 0x00, 0x00, 0x05, 0x48, 0x45, 0x4C, 0x4C, 0x4F, FOOTER]))  #hello
        # self.serial.write(bytes([HEADER, 0x00, 0x00, 5, 0x48, 0x45, 0x4C, 0x4C, 0x4F, FOOTER]))
        self.write_buff += bytes([HEADER, 0x00, 0x00, 5, 0x48, 0x45, 0x4C, 0x4C, 0x4F, FOOTER])
        # serial.write(bytes([0x48, 0x45, 0x4C, 0x4C, 0x4F]))

    def echo(self, data):
        # self.serial.write(bytes(data))
        self.write_buff += bytes(data)

    def test_bno(self):
        while True:
            print("Accelerometer (m/s^2): {}".format(self.bno.acceleration))
            print("Magnetometer (microteslas): {}".format(self.bno.magnetic))
            print("Gyroscope (rad/sec): {}".format(self.bno.gyro))
            print("Euler angle: {}".format(self.bno.euler))
            print("Quaternion: {}".format(self.bno.quaternion))
            print("Linear acceleration (m/s^2): {}".format(self.bno.linear_acceleration))
            print("Gravity (m/s^2): {}".format(self.bno.gravity))
            time.sleep(1)

    def autoreport_data(self):
        curr_time = time.monotonic()
        dt = curr_time - self.autoreport_last_time
        self.autoreport_clock -= dt
        if self.autoreport_clock <= 0:
            # report data!
            self.send_data(cmd=0x10, param=0x00, format="ffff", data=self.bno.quaternion)    #quat data
            self.send_data(cmd=0x10, param=0x01, format="fff", data=self.bno.euler)  #euler data
            self.send_data(cmd=0x10, param=0x02, format="fff", data=self.bno.linear_acceleration)    # lin accel
            self.send_data(cmd=0x10, param=0x03, format="fff", data=self.bno.gyro)    # gyro data
            self.autoreport_clock=self.autoreport_delay
        self.autoreport_last_time = curr_time

    def send_data(self, cmd=0x00, param=0x00, data=[], format=""):
        if len(data) == 0:  #WHY?
            # self.serial.write(bytes(HEADER, cmd, param, 0, FOOTER))
            self.write_buff += bytes(HEADER, cmd, param, 0, FOOTER)
        elif len(data) > 255:
            return False
        else:
            input_data = struct.pack(format, *data)
            # self.serial.write((bytes([HEADER, cmd, param, len(input_data)]) + input_data + bytes([FOOTER])))
            # print(str(data))
            self.write_buff += (bytes([HEADER, cmd, param, len(input_data)]) + input_data + bytes([FOOTER]))
            # self.serial.write_timeout(bytes([HEADER, cmd, param, len(data)]) + struct.pack(format, *data) + bytes([FOOTER]))
            # struct.pack(format, *data)
            # self.serial.write_timeout(bytes([0x01]))

    # FUNNY
    def parse_packet(self, packet):
        # serial.write("parsing".encode())
        # serial.write(bytes(read_packet.to_bytes()))
        if packet.cmd == 0x00:
            self.send_hello()
        elif packet.cmd == 0x01:
            self.echo(packet.data)
        elif packet.cmd == 0x18:
            self.update_pwm(packet.data)

    def main(self):
        # setup PWM, frequency of 50hz, 
        for i in range(6):
            self.pwms.append(pwmio.PWMOut(self.pwm_pins[i], duty_cycle=2**14*3, frequency=500, variable_frequency=False))
        time.sleep(0.1)
        # for i in range(6):
        #     self.pwms[i].duty_cycle=4369
        while True:
            if self.serial.in_waiting > 0:
                new_bytes = self.serial.read()
                for curr_byte in new_bytes:
                    self.read_packet.add_byte(curr_byte)
                    if self.read_packet.is_complete():
                        self.parse_packet(self.read_packet)
                        # parse packet!
                        self.read_packet.clear()
                        self.serial.reset_input_buffer()
            # self.autoreport_data()
            if (len(self.write_buff) > 0):
                writen = self.serial.write(self.write_buff)
                self.write_buff = self.write_buff[writen:]
                self.serial.reset_output_buffer()

    def test_bno(self):
        while True:
            print("Accelerometer (m/s^2): {}".format(self.bno.acceleration))
            print("Magnetometer (microteslas): {}".format(self.bno.magnetic))
            print("Gyroscope (rad/sec): {}".format(self.bno.gyro))
            print("Euler angle: {}".format(self.bno.euler))
            print("Quaternion: {}".format(self.bno.quaternion))
            print("Linear acceleration (m/s^2): {}".format(self.bno.linear_acceleration))
            print("Gravity (m/s^2): {}".format(self.bno.gravity))
            time.sleep(1)

rp = rp2040()
rp.main()
# test_bno()
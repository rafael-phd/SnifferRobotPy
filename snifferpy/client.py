import socket
import time
import struct
import numpy as np
from enum import IntEnum
import matplotlib.pyplot as plt
from utils import update_plot, is_value


class CommandType(IntEnum):
    NONE = 0
    CONN_END = 1
    MOTOR_CTRL = 2
    PID_LEFT = 3
    PID_RIGHT = 4
    SPEED_CTRL = 5


class RobotClient:
    MEAS_IDX = {'duration': 0,
                'speed_left': 1,
                'speed_right': 2,
                'ir_left': 3,
                'ir_right': 4,
                'control_left': 5,
                'control_right': 6}

    @staticmethod
    def get_num_measurements():
        return len(RobotClient.MEAS_IDX)

    @staticmethod
    def get_measurements_num_bytes():
        bytes_per_float = 4
        return bytes_per_float * RobotClient.get_num_measurements()

    def __init__(self, host, port):
        self.measurements = np.zeros((0,  self.get_num_measurements()))
        self.measurements_cnt = 0
        self.is_talking = False
        self.setpoints = None
        self.setpoints_type = CommandType.NONE
        self.host = host
        self.port = port
        self.sock = None

    def get_measurements_length(self):
        return self.measurements.shape[0]

    def set_setpoints(self, setpoints_type, setpoints=None, num_measurements=None):
        assert isinstance(setpoints_type, CommandType)
        assert (setpoints_type != CommandType.NONE or
                (setpoints is None and
                 isinstance(num_measurements, int) and num_measurements > 0))
        assert (setpoints_type != CommandType.MOTOR_CTRL or
                (isinstance(setpoints, np.ndarray) and
                 setpoints.ndim == 2 and
                 setpoints.shape[0] > 0 and
                 setpoints.shape[1] == 2 and
                 num_measurements is None))
        if setpoints_type == CommandType.NONE:
            self.setpoints = np.zeros((num_measurements, 0))
        else:
            self.setpoints = setpoints
        self.setpoints_type = setpoints_type
        self.init_measurements()

    def init_measurements(self):
        length = self.setpoints.shape[0]
        self.measurements = np.zeros((length, self.get_num_measurements()))
        self.measurements_cnt = 0

    def set_measurement(self, time_step, measurements):
        assert isinstance(time_step, int)
        assert 0 <= time_step < self.get_measurements_length()
        assert isinstance(measurements, tuple) and len(measurements) == self.get_num_measurements()
        assert is_value(measurements)
        for idx in RobotClient.MEAS_IDX.values():
            self.measurements[time_step, idx] = measurements[idx]
        self.measurements_cnt = self.measurements_cnt + 1

    def send(self, time_step):
        assert isinstance(self.sock, socket.socket)
        assert isinstance(time_step, int) and 0 <= time_step < self.measurements.shape[0]
        header = [int(self.setpoints_type)]
        data = self.setpoints[time_step].tolist()
        message = header + data
        print('sending: ', str(message))
        message_bin = struct.pack('B' * len(header), *header) + struct.pack('f' * len(data), *data)
        try:
            self.sock.sendall(message_bin)
        except (socket.error, socket.timeout):
            print('Failure when sending data!')
            return False
        return True

    def recv(self):
        # Receive data from the server
        response_bin = self.sock.recv(self.get_measurements_num_bytes())
        if len(response_bin) != self.get_measurements_num_bytes():
            print(f'Invalid data from server! #bytes:{len(response_bin)},data:{response_bin}')
            return None
        response = struct.unpack('f' * self.get_num_measurements(), response_bin)
        print('received: ', str(response))
        return response

    def connect(self):
        self.is_talking = True

        # Create a TCP/IP socket_server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket_server to the server's address and port
        server_address = (self.host, self.port)
        print('connecting to {} port {}'.format(*server_address))
        self.sock.connect(server_address)

    def reconnect(self):
        # Clean up the connection
        print('closing socket_server')
        self.sock.close()

        # Create a TCP/IP socket_server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket_server to the server's address and port
        server_address = (self.host, self.port)
        print('reconnecting to {} port {}'.format(*server_address))
        self.sock.connect(server_address)

    def close(self):
        header = [int(CommandType.CONN_END)]
        print('sending: ', str(header))
        message_bin = struct.pack('B' * len(header), *header)
        message_sent = False
        while not message_sent:
            try:
                self.sock.sendall(message_bin)
            except (socket.error, socket.timeout):
                print('Failure when sending data!')
                message_sent = False
                continue
            message_sent = True

        # Clean up the connection
        print('closing socket_server')
        self.sock.close()
        self.is_talking = False

    def talk(self):
        for k in range(self.setpoints.shape[0]):
            response = None
            while response is None:
                if self.send(time_step=k):
                    response = self.recv()

                if response is None:
                    self.reconnect()

            self.set_measurement(time_step=k, measurements=response)
            time.sleep(0.01)

    def talk_and_close(self):
        self.connect()
        self.talk()
        self.close()

    def plot_measurements(self, interval):
        fig, [ax1, ax3] = plt.subplots(nrows=2, ncols=1)
        ax2 = ax1.twinx()

        x = self.measurements[interval, self.MEAS_IDX['duration']]
        y1 = self.measurements[interval, self.MEAS_IDX['speed_left']]
        y2 = self.measurements[interval, self.MEAS_IDX['speed_right']]
        y3 = self.measurements[interval, self.MEAS_IDX['control_left']]
        y4 = self.measurements[interval, self.MEAS_IDX['control_right']]
        assert len(x) == len(y1) == len(y2)
        line1, = ax1.plot(x, y1, ':.', color='tab:blue', label='Speed Left')
        line2, = ax1.plot(x, y2, ':.', color='tab:orange', label='Speed Right')
        line5, = ax2.plot(x, y3, ':.', color='tab:green', label='Control Left')
        line6, = ax2.plot(x, y4, ':.', color='tab:red', label='Control Right')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Speed (mm/s)')
        ax2.set_ylabel('Amplitude')
        ax1.set_title('Motor Speed and Control')
        ax1.legend(handles=[line1, line2, line5, line6])

        x = self.measurements[interval, self.MEAS_IDX['duration']]
        y1 = self.measurements[interval, self.MEAS_IDX['ir_left']]
        y2 = self.measurements[interval, self.MEAS_IDX['ir_right']]
        assert len(x) == len(y1) == len(y2)
        line3, = ax3.plot(x, y1, ':.', color='tab:blue', label='Left')
        line4, = ax3.plot(x, y2, ':.', color='tab:orange', label='Right')
        ax3.set_xlabel('Time (s)')
        ax3.set_ylabel('Amplitude')
        ax3.set_title('IR Sensor')
        ax3.legend(handles=[line3, line4])

        return fig, [ax1, ax2, ax3], [line1, line2, line3, line4, line5, line6]

    def update_measurements(self, fig, axs, lines, interval):
        assert len(axs) == 3
        assert isinstance(lines, list) and len(lines) == 6

        update_plot(fig, axs[0], lines[0],
                    new_x=self.measurements[interval, self.MEAS_IDX['duration']],
                    new_y=self.measurements[interval, self.MEAS_IDX['speed_left']])
        update_plot(fig, axs[0], lines[1],
                    new_x=self.measurements[interval, self.MEAS_IDX['duration']],
                    new_y=self.measurements[interval, self.MEAS_IDX['speed_right']])
        update_plot(fig, axs[1], lines[4],
                    new_x=self.measurements[interval, self.MEAS_IDX['duration']],
                    new_y=self.measurements[interval, self.MEAS_IDX['control_left']])
        update_plot(fig, axs[1], lines[5],
                    new_x=self.measurements[interval, self.MEAS_IDX['duration']],
                    new_y=self.measurements[interval, self.MEAS_IDX['control_right']])
        update_plot(fig, axs[2], lines[2],
                    new_x=self.measurements[interval, self.MEAS_IDX['duration']],
                    new_y=self.measurements[interval, self.MEAS_IDX['ir_left']])
        update_plot(fig, axs[2], lines[3],
                    new_x=self.measurements[interval, self.MEAS_IDX['duration']],
                    new_y=self.measurements[interval, self.MEAS_IDX['ir_right']])

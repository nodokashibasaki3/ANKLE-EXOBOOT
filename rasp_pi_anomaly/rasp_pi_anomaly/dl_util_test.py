import exoboot
from typing import Type
import constants
import numpy as np
import socket
import time
from collections import deque


class JetsonInterface:

    def __init__(self, do_set_up_server=True, server_ip='192.168.1.2', recv_port=8080):
        self.data = deque(maxlen=10)
        if do_set_up_server:
            self.client_socket = self.setup_connection(server_ip, recv_port)

    def setup_connection(self, server_ip, recv_port):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, recv_port))
        return client_socket

    def send_full_message(self, message):
        msg = message.encode('utf-8')
        header = len(msg).to_bytes(4, 'big')
        self.client_socket.sendall(header + msg)

    def package_message(self, side: Type[constants.Side], data: exoboot.Exo.DataContainer):
        features = self.prep_features(data)
        message = '!' + str(side.value) +  '!' + features 
        return message

    def package_and_send_message(self, side, data_container):
        message = self.package_message(side=side, data=data_container)
        self.send_full_message(message)

    def grab_message_and_parse(self):
        header = self.client_socket.recv(4)
        message_length = int.from_bytes(header, 'big')
        predictions = self.client_socket.recv(message_length).decode('utf-8')
        side, pred1, pred2 = map(float, predictions.split(","))
        self.data.appendleft([side, pred1, pred2])

    def get_most_recent_gait_phase(self, side: Type[constants.Side]):
        for message in self.data:
            if side == constants.Side.LEFT and int(message[0]) == 0:
                gait_phase = message[1]
                stance_swing = message[2]
                return gait_phase, stance_swing
            elif side == constants.Side.RIGHT and int(message[0]) == 1:
                gait_phase = message[1]
                stance_swing = message[2]
                return gait_phase, stance_swing
        return None, None

    def prep_features(self, data):
        # Based on your prep_features method
        main_accel_z = '%.5f' % data.accel_z
        main_gyro_z = '%.5f' % data.gyro_z
        main_ankle_angle = '%.5f' % data.ankle_angle
        main_ankle_velocity = '%.5f' % data.ankle_velocity
        
        main_accel_x = '%.5f' % data.accel_x
        main_accel_y = '%.5f' % data.accel_y
        main_gyro_x = '%.5f' % data.gyro_x
        main_gyro_y = '%.5f' % data.gyro_y
            
        features = ','.join([main_accel_x, main_accel_y, main_accel_z, main_gyro_x, main_gyro_y, main_gyro_z, main_ankle_angle, main_ankle_velocity])
        return features

    def run(self, side, data_container, DATA_SEND_COUNT_BEFORE_PREDICTION=80):
        send_counter = 0
        try:
            while True:
                for _ in range(DATA_SEND_COUNT_BEFORE_PREDICTION):
                    self.package_and_send_message(side, data_container)
                    send_counter += 1
                    print(f"Sent data {send_counter}")
                    time.sleep(0.005)
                
                self.grab_message_and_parse()
                gait_phase, stance_swing = self.get_most_recent_gait_phase(side)
                print("Received predictions:", gait_phase, stance_swing)

        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            self.client_socket.close()


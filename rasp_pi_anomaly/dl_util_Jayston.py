import exoboot
from typing import Type
import constants
import numpy as np
import tcpip
from collections import deque


class JetsonInterface():

    def __init__(self, do_set_up_server=True, server_ip='192.168.1.2', recv_port=8080,
                 do_gp_sp_isp_bilateral=False, do_velocity_bilateral=False, do_ramp_bilateral=False):
        self.data = deque(maxlen=10)
        if do_set_up_server:
            self.clienttcp = tcpip.ClientTCP(server_ip, recv_port)

        if do_gp_sp_isp_bilateral: gp_sp_isp_message = '2'
        else: gp_sp_isp_message = '1'
        if do_velocity_bilateral: velocity_message = '2'
        else: velocity_message = '1'
        if do_ramp_bilateral: ramp_message = '2'
        else: ramp_message = '1'
        message = '|' + gp_sp_isp_message + '|' + velocity_message + '|' + ramp_message

        self.clienttcp.to_server(msg=message)


    def package_message(self, side: Type[constants.Side], 
                        data: exoboot.Exo.DataContainer, other_data_container: exoboot.Exo.DataContainer,
                        do_gp_sp_isp_bilateral=False, do_velocity_bilateral=False, do_ramp_bilateral=False):
        
        get_gp_sp_isp_features = self.prep_features(data, other_data_container, do_gp_sp_isp_bilateral, label=1)
        get_velocity_features = self.prep_features(data, other_data_container, do_velocity_bilateral, label=2)
        get_ramp_features = self.prep_features(data, other_data_container, do_ramp_bilateral, label=3)

        message = '!' + get_gp_sp_isp_features + '!' + get_velocity_features + '!' + get_ramp_features + '!' + str(side.value)
        return message

    def package_and_send_message(self, side, data_container, other_data_container, 
                                 do_gp_sp_isp_bilateral, do_velocity_bilateral, do_ramp_bilateral):
        message = self.package_message(side=side, data=data_container, other_data_container=other_data_container,
                        do_gp_sp_isp_bilateral=do_gp_sp_isp_bilateral, do_velocity_bilateral=do_velocity_bilateral, do_ramp_bilateral=do_ramp_bilateral)
        self.clienttcp.to_server(msg=message)

    def grab_message_and_parse(self):
        message = self.clienttcp.from_server()
        self.parse(message)

    def parse(self, message):
        '''parses message from jetson. Returns side, gait_phase, is_stance'''
        if message is not None and len(message) != 0 and 'None' not in message:
            print(message)
            if message[0] == '!':
                message_list = message.split("!")[1:]
                for message in message_list:
                    data_list = message.split(",")
                    self.data.appendleft([float(i) for i in data_list])
                    # print(data_list)

    def get_most_recent_gait_phase(self, side: Type[constants.Side]):
        for message in self.data:
            if side == constants.Side.LEFT and message[0] == 0:
                gait_phase = message[1]
                stance_swing = message[2]
                return gait_phase, stance_swing
            elif side == constants.Side.RIGHT and message[0] == 1:
                gait_phase = message[1]
                stance_swing = message[2]
                return gait_phase, stance_swing
    
    def prep_features(self, data, other_data_container, do_bilateral, label=0):
        
        main_accel_z = '%.5f' % data.accel_z
        main_gyro_z = '%.5f' % data.gyro_z
        main_ankle_angle = '%.5f' % data.ankle_angle
        main_ankle_velocity = '%.5f' % data.ankle_velocity
        if do_bilateral:
            other_accel_z = '%.5f' % other_data_container.accel_z
            other_gyro_z = '%.5f' % other_data_container.gyro_z
            other_ankle_angle = '%.5f' % other_data_container.ankle_angle
            other_ankle_velocity = '%.5f' % other_data_container.ankle_velocity
        if label == 1:
            main_accel_x = '%.5f' % data.accel_x
            main_accel_y = '%.5f' % data.accel_y
            main_gyro_x = '%.5f' % data.gyro_x
            main_gyro_y = '%.5f' % data.gyro_y
            if do_bilateral:
                other_accel_x = '%.5f' % other_data_container.accel_x
                other_accel_y = '%.5f' % other_data_container.accel_y
                other_gyro_x = '%.5f' % other_data_container.gyro_x
                other_gyro_y = '%.5f' % other_data_container.gyro_y
                features = main_accel_x + ',' + main_accel_y + ',' + main_accel_z + ',' + \
                        main_gyro_x + ',' + main_gyro_y + ',' + main_gyro_z + ',' + main_ankle_angle + ',' + main_ankle_velocity + ',' +\
                        other_accel_x + ',' + other_accel_y + ',' + other_accel_z + ',' + other_gyro_x + ',' + other_gyro_y + ',' + \
                        other_gyro_z + ',' + other_ankle_angle + ',' + other_ankle_velocity + ',' + str(label) + ',' + '2'
            else:
                features = main_accel_x + ',' + main_accel_y + ',' + main_accel_z + ',' + \
                        main_gyro_x + ',' + main_gyro_y + ',' + main_gyro_z + ',' + main_ankle_angle + ',' + main_ankle_velocity + ',' +\
                        str(label) + ',' + '1'
        elif label == 2 or label == 3:
            if do_bilateral:
                features = main_accel_z + ',' + main_gyro_z + ',' + main_ankle_angle + ',' + main_ankle_velocity + ',' + other_accel_z + \
                         ',' + other_gyro_z + ',' + other_ankle_angle + ',' + other_ankle_velocity + ',' + str(label) + ',' + '2'
            else:
                features = main_accel_z + ',' + main_gyro_z + ',' + main_ankle_angle + ',' + main_ankle_velocity + ',' + str(label) + ',' + '1'
        
        return features
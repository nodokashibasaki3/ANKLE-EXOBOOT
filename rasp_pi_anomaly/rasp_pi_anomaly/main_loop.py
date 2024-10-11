'''
This is the main GT program for running the Dephy exos. Read the Readme.
'''
import exoboot
import threading
import controllers
import state_machines
import gait_state_estimators
import constants
import filters
import time
import util
import config_util
import parameter_passers
import control_muxer
#import control_muxer_Jayston
import plotters
import ml_util
import traceback
import pandas as pd
import offline_testing_file
import os

config, offline_test_time_duration, past_data_file_names = config_util.load_config_from_args()   # loads config from passed args
#config, offline_test_time_duration, past_data_file_names, control_muxer = config_util.load_config_from_args()

IS_HARDWARE_CONNECTED = config.IS_HARDWARE_CONNECTED
offline_data_left, offline_data_right = None, None
if not IS_HARDWARE_CONNECTED:
    offline_data_left, offline_data_right = offline_testing_file.get_offline_past_data_files(config.IS_HARDWARE_CONNECTED, past_data_file_names, offline_test_time_duration)

file_ID = input(
    'Other than the date, what would you like added to the filename?')

'''if sync signal is used, this will be gpiozero object shared between exos.'''
sync_detector = config_util.get_sync_detector(config)

'''Connect to Exos, instantiate Exo objects.'''
exo_list = exoboot.connect_to_exos(IS_HARDWARE_CONNECTED,
    file_ID=file_ID, config=config, sync_detector=sync_detector, offline_data_left=offline_data_left, offline_data_right=offline_data_right)
if IS_HARDWARE_CONNECTED:
    print('Battery Voltage: ', 0.001*exo_list[0].get_batt_voltage(), 'V')

config_saver = config_util.ConfigSaver(
    file_ID=file_ID, config=config)  # Saves config updates

'''Instantiate gait_state_estimator and state_machine objects, store in lists.'''


gait_state_estimator_list, state_machine_list = control_muxer.get_gse_and_sm_lists(
    exo_list=exo_list, config=config)

'''Prep parameter passing.'''
lock = threading.Lock()
quit_event = threading.Event()
new_params_event = threading.Event()
# v0.2,15,0.56,0.6!

'''Perform standing calibration.'''
if IS_HARDWARE_CONNECTED:
    if not config.READ_ONLY:
        for exo in exo_list:
            standing_angle = exo.standing_calibration()
            if exo.side == constants.Side.LEFT:
                config.LEFT_STANDING_ANGLE = standing_angle
            else:
                config.RIGHT_STANDING_ANGLE = standing_angle
    else:
        print('Not calibrating... READ_ONLY = True in config')
else:
    try:
        config_file = pd.read_csv(str(past_data_file_names) + '_CONFIG.csv')
        config.LEFT_STANDING_ANGLE = config_file['LEFT_STANDING_ANGLE'][0]
        config.RIGHT_STANDING_ANGLE = config_file['RIGHT_STANDING_ANGLE'][0]
    except:
        raise ValueError('Past Config File, required to be passed as arguments, not found in local directory.')
    for exo in exo_list:
        if exo.side == constants.Side.LEFT:
            if 'LEFT_MOTOR_OFFSET' in config_file.columns:
                config.LEFT_MOTOR_OFFSET = config_file['LEFT_MOTOR_OFFSET'][0]
            else:
                config.LEFT_MOTOR_OFFSET = 0
            motor_offset = config.LEFT_MOTOR_OFFSET
        else:
            if 'RIGHT_MOTOR_OFFSET' in config_file.columns:
                config.RIGHT_MOTOR_OFFSET = config_file['RIGHT_MOTOR_OFFSET'][0]
            else:
                config.RIGHT_MOTOR_OFFSET = 0
            motor_offset = config.RIGHT_MOTOR_OFFSET
        exo.standing_calibration_offline(motor_offset)
    
input('\nPress any key to begin\n')
print('Start!\n')

'''Main Loop: Check param updates, Read data, calculate gait state, apply control, write data.'''
timer = util.FlexibleTimer(
    target_freq=config.TARGET_FREQ)  # attempts constants freq
t0 = time.perf_counter()
keyboard_thread = parameter_passers.ParameterPasser(
    lock=lock, config=config, quit_event=quit_event,
    new_params_event=new_params_event)
config_saver.write_data(loop_time=0)  # Write first row on config
only_write_if_new = not config.READ_ONLY and config.ONLY_LOG_IF_NEW
iteration_count = 0
exit_code = False

while True:
    try:
        timer.pause()
        if IS_HARDWARE_CONNECTED:
            loop_time = time.perf_counter() - t0
        else:
            ##print(offline_data_left.columns)
            loop_time = offline_data_left['loop_time'][iteration_count]
        lock.acquire()
        if new_params_event.is_set():
            config_saver.write_data(loop_time=loop_time)  # Update config file
            for state_machine in state_machine_list:  # Make sure up to date
                state_machine.update_ctrl_params_from_config(config=config)
            for gait_state_estimator in gait_state_estimator_list:  # Make sure up to date
                gait_state_estimator.update_params_from_config(config=config)
            new_params_event.clear()
        if quit_event.is_set(): # If user enters "quit"
            exit_code = True  
        lock.release()

        for exo in exo_list:
            if not IS_HARDWARE_CONNECTED:
                if exo.side == constants.Side.LEFT:
                    loop_time = offline_data_left['loop_time'][iteration_count]
                else:
                    loop_time = offline_data_right['loop_time'][iteration_count]
            exo.read_data(exo_boot_side=exo.side, iteration_count=iteration_count, loop_time=loop_time)
        for gait_state_estimator in gait_state_estimator_list:
            gait_state_estimator.detect()
        if not config.READ_ONLY:
            for state_machine in state_machine_list:
                state_machine.step(read_only=config.READ_ONLY)
        for exo in exo_list:
            exo.write_data(only_write_if_new=only_write_if_new)
        if not IS_HARDWARE_CONNECTED:
            iteration_count = iteration_count + 1
            if offline_test_time_duration:
                if loop_time > float(offline_test_time_duration):
                    break
            else: 
                if iteration_count == len(offline_data_left) or iteration_count == len(offline_data_right):
                    break
        if exit_code:
            break
    except KeyboardInterrupt:
        print('Ctrl-C detected, Exiting Gracefully')
        break
    except Exception as err:
        print(traceback.print_exc())
        print("Unexpected error:", err)
        break

'''Safely close files, stop streaming, optionally saves plots'''
config_saver.close_file()
for exo in exo_list:
    exo.close()
if config.VARS_TO_PLOT:
    plotters.save_plot(filename=exo_list[0].filename.replace(
        '_LEFT.csv', '').replace('_RIGHT.csv', ''), vars_to_plot=config.VARS_TO_PLOT)

filename = exo_list[0].filename.replace('_LEFT.csv', '').replace('_RIGHT.csv', '')
iter_vars, count = ['_LEFT.csv', '_RIGHT.csv'], 0

left_file = filename+iter_vars[0]
right_file = filename+iter_vars[1]
 
if config.DO_INCLUDE_VNMC_DATA or not config.DO_INCLUDE_EXO_ADD_DATA:
    while True:
        if (left_file.split('/')[-1] in os.listdir('exo_data')) and (right_file.split('/')[-1] in os.listdir('exo_data')): 
            break
    for state_machine in state_machine_list:
        path = filename+iter_vars[count]
        df = pd.DataFrame(pd.read_csv(path))
        if config.DO_INCLUDE_VNMC_DATA:
            df = pd.concat([df, pd.DataFrame(state_machine.stance_controller.vnmc_dict)], axis=1, join='inner')
        if not config.DO_INCLUDE_EXO_ADD_DATA:
            df.drop(columns=['commanded_voltage', 'commanded_motor_impedance',
                            'controller', 'control_state'], inplace=True)
        count += 1
        df.to_csv(path, index=False)

print('Done!!!')

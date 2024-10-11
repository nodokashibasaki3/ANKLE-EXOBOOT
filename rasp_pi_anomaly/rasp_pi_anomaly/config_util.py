from typing import Type, List
from dataclasses import dataclass, field
import time
import csv
import sys
import importlib
from enum import Enum
import argparse
import constants
import platform
from gpiozero import InputDevice, BadPinFactory

class Task(Enum):
    '''Used to determine gait_event_detector used and state machines used.'''
    WALKING = 0
    STANDINGPERTURBATION = 1
    BILATERALSTANDINGPERTURBATION = 2
    SLIPDETECTFROMSYNC = 3
    WALKINGMLGAITPHASE = 4
    WALKJOGDLGAITPHASE = 5
    ANOMALY = 6

class StanceCtrlStyle(Enum):
    '''Used to determine behavior during stance.'''
    FOURPOINTSPLINE = 0
    GENERICSPLINE = 1
    SAWICKIWICKI = 2
    GENERICIMPEDANCE = 3
    FIVEPOINTSPLINE = 4
    VIRTUALNEUROMUSCULARCONTROLLER = 5


@dataclass
class ConfigurableConstants():
    '''Class that stores configuration-related constants.

    These variables serve to allow 1) loadable configurations from files in /custom_constants/, 
    2) online updating of device behavior via parameter_passers.py, and 3) to store calibration 
    details. Below are the default config constants. DO NOT MODIFY DEFAULTS. Write your own short
    script in /custom_constants/ (see default_config.py for example).
    (see )  '''
    # Set by functions... no need to change in config file
    loop_time: float = 0
    actual_time: float = time.time()
    LEFT_STANDING_ANGLE: float = None  # Deg
    RIGHT_STANDING_ANGLE: float = None  # Deg

    TARGET_FREQ: float = 175  # Hz
    ACTPACK_FREQ: float = 200  # Hz
    DO_DEPHY_LOG: bool = False
    DEPHY_LOG_LEVEL: int = 4
    ONLY_LOG_IF_NEW: bool = True

    # TASK: Type[Task] = Task.WALKJOGDLGAITPHASE
    TASK: Type[Task] = Task.WALKING
    # TASK: Type[Task] = Task.ANOMALY

    STANCE_CONTROL_STYLE: Type[StanceCtrlStyle] = StanceCtrlStyle.FOURPOINTSPLINE
    MAX_ALLOWABLE_CURRENT = 20000  # mA

    # Gait State details
    HS_GYRO_THRESHOLD: float = 100
    HS_GYRO_FILTER_N: int = 2
    HS_GYRO_FILTER_WN: float = 3
    HS_GYRO_DELAY: float = 0.05
    SWING_SLACK: int = 5000
    # TOE_OFF_FRACTION: float = 0.60
    #for actuated running
    TOE_OFF_FRACTION: float = 0.60

    REEL_IN_MV: int = 2400
    REEL_IN_SLACK_CUTOFF: int = 1200
    REEL_IN_TIMEOUT: float = 0.2
    NUM_STRIDES_REQUIRED: int = 2
    SWING_ONLY: bool = False
    

    # 4 point Spline
    RISE_FRACTION: float = 0.2
    PEAK_FRACTION: float = 0.53
    FALL_FRACTION: float = 0.60
    PEAK_TORQUE: float = 25

    #for jogging/running actuated
    # RISE_FRACTION: float = 0.05
    # PEAK_FRACTION: float = 0.2
    # FALL_FRACTION: float = 0.4
    # PEAK_TORQUE: float = 25
    SPLINE_BIAS: float = 3  # Nm

    # Impedance
    K_VAL: int = 500
    B_VAL: int = 0
    B_RATIO: float = 0.5  # when B_VAL is a function of B_RATIO. 2.5 is approx. crit. damped
    SET_POINT: float = 0  # Deg

    READ_ONLY: bool = False  # Does not require Lipos
    DO_READ_FSRS: bool = False
    DO_READ_SYNC: bool = True

    PRINT_HS: bool = True  # Print heel strikes
    VARS_TO_PLOT: List = field(default_factory=lambda: [])
    DO_DETECT_SLIP: bool = False
    SLIP_DETECT_ACTIVE: bool = False
    DO_INCLUDE_GEN_VARS: bool = False
    SLIP_DETECT_DELAY: int = 0
    DO_FILTER_GAIT_PHASE: bool = False

    # Offline Testing Parameter
    IS_HARDWARE_CONNECTED: bool = True
    LEFT_MOTOR_OFFSET: float = 0
    RIGHT_MOTOR_OFFSET: float = 0

    # VNMC Parameters
    SCALING_FACTOR: float = 1
    VNMC_GAIN: float = 1
    MUSCLE_UPDATE_FREQUENCY: int = 1
    DO_INCLUDE_VNMC_DATA: bool = True if STANCE_CONTROL_STYLE == StanceCtrlStyle.VIRTUALNEUROMUSCULARCONTROLLER else False

    # DL Gait State Estimator Parameters
    DO_GP_SP_ISP_BILATERAL = True
    DO_VELOCITY_BILATERAL = False
    DO_RAMP_BILATERAL = True
    SERVER_IP = '169.254.241.134'
    PORT = 10000

    # Include Additional Exo Data (For Debugging Purposes)
    DO_INCLUDE_EXO_ADD_DATA: bool = False
    MLE_SPLINE_CONTROLLER: bool  = False
    

    EXPERIMENTER_NOTES: str = 'Experimenter notes go here'


class ConfigSaver():
    def __init__(self, file_ID: str, config: Type[ConfigurableConstants]):
        '''file_ID is used as a custom file identifier after date.'''
        self.file_ID = file_ID
        self.config = config
        subfolder_name = 'exo_data/'
        filename = subfolder_name + \
            time.strftime("%Y%m%d_%H%M_") + file_ID + \
            '_CONFIG' + '.csv'
        self.my_file = open(filename, 'w', newline='')
        self.writer = csv.DictWriter(
            self.my_file, fieldnames=self.config.__dict__.keys())
        self.writer.writeheader()

    def write_data(self, loop_time):
        '''Writes new row of Config data to Config file.'''
        self.config.loop_time = loop_time
        self.config.actual_time = time.time()
        self.writer.writerow(self.config.__dict__)

    def close_file(self):
        if self.file_ID is not None:
            self.my_file.close()


def load_config(config_filename, offline_value, hardware_connected) -> tuple[any, any]:
    
    try:
        # strip extra parts off
        config_filename = config_filename.lower()
        if config_filename.endswith('_config'):
            config_filename = config_filename[:-7]
        elif config_filename.endswith('_config.py'):
            config_filename = config_filename[:-10]
        elif config_filename.endswith('.py'):
            config_filename = config_filename[:-4]
        config_filename = config_filename + '_config'
        module = importlib.import_module('.' + config_filename, package='custom_configs')
    except:
        error_str = 'Unable to find config file: ' + \
            config_filename + ' in custom_config'
        raise ValueError(error_str)
    config = module.config
    
    if hardware_connected == 'True':
        config.IS_HARDWARE_CONNECTED = True
    elif hardware_connected == 'False':
        config.IS_HARDWARE_CONNECTED = False
    else: 
        print('Hardware Connection Status not interpretable.')
        quit()
    print('Using ConfigurableConstants from: ', config_filename)
    print(f"Loaded configuration: {config}")

    if offline_value:
        try:
            offline_test_time_duration = float(offline_value)
            print('\nOffline Test Time Duration = ' + str(offline_test_time_duration) + ' seconds.\n')
        except: 
            print('Offline Test Time Duration should be an integer or float value.')
            quit()
    else: offline_test_time_duration = offline_value

    return config, offline_test_time_duration


def parse_args():
    # Create the parser
    my_parser = argparse.ArgumentParser(prog='Exoboot Code',
                                        description='Run Exoboot Controllers',
                                        epilog='Enjoy the program! :)')
    # Add the arguments
    my_parser.add_argument('-hd', '--hardwareconnected', action='store',
                           type=str, required=False, default='True')
    my_parser.add_argument('-ot', '--offlinetesttime', action='store',
                           type=str, required=False, default=False)
    my_parser.add_argument('-pf', '--past_data_file_names', action='store',
                           type=str, required=False, default='Default_Past_Data')
    my_parser.add_argument('-c', '--config', action='store',
                           type=str, required=False, default='default_config')
    # Execute the parse_args() method
    args = my_parser.parse_args()
    return args

# def parse_args():
#     # Create the parser
#     my_parser = argparse.ArgumentParser(prog='Exoboot Code',
#                                         description='Run Exoboot Controllers',
#                                         epilog='Enjoy the program! :)')
#     # Add the arguments
#     my_parser.add_argument('-hd', '--hardwareconnected', action='store',
#                            type=str, required=False, default='True')
#     my_parser.add_argument('-ot', '--offlinetesttime', action='store',
#                            type=str, required=False, default=False)
#     my_parser.add_argument('-pf', '--past_data_file_names', action='store',
#                            type=str, required=False, default='Default_Past_Data')
#     my_parser.add_argument('-c', '--config', action='store',
#                            type=str, required=False, default='default_config')
#     # New argument for control muxer selection
#     my_parser.add_argument('-cm', '--controlmuxer', action='store',
#                            type=str, required=False, default='control_muxer',
#                            help='Choose the control muxer file: control_muxer or control_muxer_Jayston')

#     # Execute the parse_args() method
#     args = my_parser.parse_args()
#     return args


##CHANGES: depending on the online/offline mode it chooses which config to load##
def load_config_from_args():
    args = parse_args()

    if args.config.lower() == "offline":
        config_file = "offline_config"
    else:
        config_file = "online_config"

    config, offline_test_time_duration = load_config(
        config_filename=config_file,
        offline_value=args.offlinetesttime,
        hardware_connected=args.hardwareconnected
    )
    
    print(f"Selected config file: {config_file}")

    return config, offline_test_time_duration, args.past_data_file_names

# def load_config_from_args():
#     args = parse_args()

#     # Determine which config file to use
#     if args.config.lower() == "offline":
#         config_file = "offline_config"
#     else:
#         config_file = "online_config"

#     config, offline_test_time_duration = load_config(
#         config_filename=config_file,
#         offline_value=args.offlinetesttime,
#         hardware_connected=args.hardwareconnected
#     )

#     #  determining which control muxer to load
#     if args.controlmuxer.lower() == "control_muxer_jayston":
#         control_muxer = importlib.import_module('control_muxer_Jayston')
#     else:
#         control_muxer = importlib.import_module('control_muxer')

#     print(f"Selected config file: {config_file}")
#     print(f"Selected control muxer: {args.controlmuxer}")

#     return config, offline_test_time_duration, args.past_data_file_names, control_muxer

def get_sync_detector(config):
    if config.IS_HARDWARE_CONNECTED and (platform.system() == "Linux" and "arm" in platform.machine()):
        try:
            sync_detector = InputDevice(pin=config.SYNC_PIN)
            return sync_detector
        except BadPinFactory as e:
            print(f"Error initializing gpiozero: {e}")
            sys.exit(1)
    else:
        # Return a mock object or None for offline mode
        print("Running in offline mode: Sync detector not initialized.")
        return None


'''
def get_sync_detector(config: Type[ConfigurableConstants]):
    if config.DO_READ_SYNC:
        print('Creating sync detector')
        import gpiozero  # pylint: disable=import-error
        sync_detector = gpiozero.InputDevice(
            pin=constants.SYNC_PIN, pull_up=False)
        return sync_detector
    else:
        return None
'''
import threading
from typing import Type
import config_util


class ParameterPasser(threading.Thread):
    def __init__(self,
                 lock: Type[threading.Lock],
                 config: Type[config_util.ConfigurableConstants],
                 quit_event: Type[threading.Event],
                 new_params_event: Type[threading.Event],
                 name='keyboard-input-thread'):
        '''This class passes parameters via user input and a parallel thread.

        The general idea is that this thread waits for an input, then grabs a lock (to stop the main thread),
        checks if the message follows the "code" (starts with 'v', ends with '!'), and then updates config
        params, depending on which params your child class wants updated. Then it sets the new_param_event flag
        to signal to the main loop to update the controllers'''
        super().__init__(name=name)
        self.daemon = True  # Thread property
        self.lock = lock
        self.config = config
        self.quit_event = quit_event
        self.new_params_event = new_params_event
        self.start()  # Starts the run() function

    # This run function overrides the run() function in threading.Thread
    def run(self):
        while True:
            msg = input()
            if msg == 'a':
                self.lock.acquire()
                self.config.SLIP_DETECT_ACTIVE = not self.config.SLIP_DETECT_ACTIVE
                self.config.SWING_ONLY = not self.config.SWING_ONLY
                print('swing only: ', self.config.SWING_ONLY,
                      'slip detect active: ', self.config.SWING_ONLY)
                self.new_params_event.set()
                self.lock.release()

            elif msg == 's':
                print('Changing Speed')
                self.lock.acquire()
                self.new_params_event.set()
                self.lock.release()

            elif len(msg) < 3:
                print('Message must be either "quit" or a string of parameters'
                      ' starting with a letter (v for splines, k for stiffness,'
                      ' s for setpoint) and ending with an exclamation point)')

            elif msg.lower() == 'quit':
                print('Quitting')
                self.lock.acquire()
                self.quit_event.set()
                self.config.SLIP_DETECT_ACTIVE = not self.config.SLIP_DETECT_ACTIVE
                if not self.config.SWING_ONLY: self.config.SWING_ONLY = not self.config.SWING_ONLY
                self.new_params_event.set()
                self.lock.release()
                break

            elif msg[-1] == '!':
                self.lock.acquire()
                first_letter = msg[0]
                msg_content = msg[1:-1]

                if first_letter == 'v':
                    param_list = [float(x) for x in msg_content.split(',')]
                    if len(param_list) != 4:
                        print('Must send four spline points with v<>! message')
                    else:
                        self.config.RISE_FRACTION = param_list[0]
                        self.config.PEAK_TORQUE = param_list[1]
                        self.config.PEAK_FRACTION = param_list[2]
                        self.config.FALL_FRACTION = param_list[3]
                elif first_letter == 'k':
                    if msg_content.isdigit():
                        self.config.K_VAL = int(msg_content)
                        self.config.B_VAL = self.config.B_RATIO * \
                            self.config.K_VAL  # 2.5ish = critically damped
                        print('k_val updated to: ', msg_content)
                    else:
                        print('Must provide single positive integer to update k_val')
                elif first_letter == 's':
                    if msg_content.lstrip('-').isdigit():
                        self.config.SET_POINT = int(msg_content)
                        print('SET_POINT updated to: ', msg_content)
                    else:
                        print('Must provide single integer to update SET_POINT')
                elif first_letter == 'p':
                    if msg_content.isdigit():
                        if 0 <= int(msg_content) <= 40:
                            self.config.PEAK_TORQUE = int(msg_content)
                            print('Peak torque set to: ',
                                  self.config.PEAK_TORQUE)
                    else:
                        print('Must provide single integer to update PEAK_TORQUE')
                elif first_letter == 'd':
                    # Delay for slip detectors
                    self.config.SLIP_DETECT_DELAY = int(msg_content)
                elif first_letter == '-':
                    self.config.EXPERIMENTER_NOTES = msg_content
                    print('Added that message to the config.')
                self.new_params_event.set()
                self.lock.release()

            elif msg[-1] == '|':
                self.lock.acquire()
                first_letter = msg[0]
                msg_content = msg[1:-1]

                try: msg_content = float(msg_content)
                except: pass

                if first_letter == 's':
                    if isinstance(msg_content, float):
                        self.config.SCALING_FACTOR = msg_content
                        print('Scaling Factor set to: ', self.config.SCALING_FACTOR)
                    else:
                        print('Must provide single float or integer value to update SCALING_FACTOR')
                elif first_letter == 'g':
                    if isinstance(msg_content, float):
                        self.config.VNMC_GAIN = msg_content
                        print('VNMC Gain set to: ', self.config.VNMC_GAIN)
                    else:
                        print('Must provide single float or integer value to update VNMC_GAIN')
                elif first_letter == 'n':
                    if isinstance(msg_content, float):
                        self.config.MUSCLE_UPDATE_FREQUENCY = int(msg_content)
                        print('Muscle Update Frequency set to: ', self.config.MUSCLE_UPDATE_FREQUENCY)
                    else:
                        print('Must provide single integer to update MUSCLE_UPDATE_FREQUENCY')
                self.new_params_event.set()
                self.lock.release()

            else:
                print('IDK how to interpret your message')

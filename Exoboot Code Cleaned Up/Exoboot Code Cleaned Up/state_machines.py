from typing import Type

import numpy as np

import constants
import controllers
import filters
import gait_state_estimators
from exoboot import Exo
import util
import config_util


class HighLevelController():
    '''A class that steps through controllers depending on, for instance, gait events.'''

    def __init__(self,
                 exo: Type[Exo]):
        self.exo = exo

    def step(self, read_only):
        '''Primary function to step through mid-level controllers.'''
        raise ValueError('step() not written yet for this controller')

    def update_ctrl_params_from_config(self, config):
        '''A function to update mid-level control params from the config object.'''
        raise ValueError(
            'update_ctrl_params_from_config() not written yet for this controller')


class StandingPerturbationResponse(HighLevelController):
    '''Pass through high level controller that implements standing perturbation response.'''

    def __init__(self,
                 exo: Type[Exo],
                 standing_controller: Type[controllers.Controller],
                 slip_controller: Type[controllers.Controller],
                 standing_controller_used,
                 slip_controller_used,
                 slip_recovery_time: float = 1.5):
        self.controller_used = None
        self.control_state = None
        self.exo = exo
        self.standing_controller = standing_controller
        self.slip_controller = slip_controller
        self.slip_ctrl_timer = util.DelayTimer(delay_time=slip_recovery_time)
        self.controller_now = self.standing_controller
        self.standing_controller_used, self.slip_controller_used = standing_controller_used, slip_controller_used

    def step(self, read_only):
        '''uses slip detector to detect slip onset, uses timer to stop slip controller.'''

        if self.slip_ctrl_timer.check():
            if self.exo.side == constants.Side.LEFT:
                print('slip timeout--moving back now')
            # If slip controller time has elapsed (goes True) and we need to switch back
            self.slip_ctrl_timer.reset()
            self.controller_now = self.standing_controller
            did_controllers_switch = True
            self.controller_used = self.standing_controller_used
            self.control_state = constants.ControlState.StandingState.value
        elif self.exo.data.did_slip:
            self.slip_ctrl_timer.start()
            self.controller_now = self.slip_controller
            did_controllers_switch = True
            self.controller_used = self.slip_controller_used
            self.control_state = constants.ControlState.SlipState.value
        else:
            did_controllers_switch = False

        self.exo.data.controller = self.controller_used
        self.exo.data.control_state = self.control_state

        if not read_only:
            self.controller_now.command(reset=did_controllers_switch)

    def update_ctrl_params_from_config(self, config):
        self.slip_controller.update_ctrl_params_from_config(config=config)


class StanceSwingStateMachine(HighLevelController):
    '''Unilateral state machine that takes in data, segments strides, and applies controllers'''

    def __init__(self,
                 exo: Type[Exo],
                 stance_controller: Type[controllers.Controller],
                 swing_controller: Type[controllers.Controller],
                 stance_controller_used, swing_controller_used
                 ):
        '''A state machine object is associated with an exo, and reads/stores exo data, applies logic to
        determine gait states and phases, chooses the correct controllers, and applies the
        controller.'''
        self.controller_used = None
        self.control_state = None
        self.exo = exo
        self.stance_controller = stance_controller
        self.swing_controller = swing_controller
        self.controller_now = self.swing_controller
        self.stance_controller_used, self.swing_controller_used = stance_controller_used, swing_controller_used

    def step(self, read_only=False):
        # Check state machine transition criteria, switching controller_now if criteria are met
        if (self.controller_now == self.swing_controller and
            self.exo.data.did_heel_strike and
                self.exo.data.gait_phase is not None):
            self.controller_now = self.stance_controller
            did_controllers_switch = True
            self.controller_used = self.stance_controller_used
            self.control_state = constants.ControlState.StanceState.value
        elif self.exo.data.did_toe_off or self.exo.data.gait_phase is None:
            self.controller_now = self.swing_controller
            did_controllers_switch = True
            self.controller_used = self.swing_controller_used
            self.control_state = constants.ControlState.SwingState.value
        else:
            did_controllers_switch = False

        self.exo.data.controller = self.controller_used
        self.exo.data.control_state = self.control_state

        if not read_only:
            self.controller_now.command(reset=did_controllers_switch)

    def update_ctrl_params_from_config(self, config):
        self.stance_controller.update_ctrl_params_from_config(config=config)


class StanceSwingReeloutReelinStateMachine(HighLevelController):
    '''Unilateral state machine that takes in data, segments strides, and applies controllers'''

    def __init__(self,
                 exo: Exo,
                 stance_controller: Type[controllers.Controller],
                 swing_controller: Type[controllers.Controller],
                 reel_out_controller: Type[controllers.Controller],
                 reel_in_controller: Type[controllers.Controller],
                 reel_in_controller_used,
                 swing_controller_used,
                 reel_out_controller_used,
                 stance_controller_used,
                 config,
                 swing_only=False
                 ):
        '''A state machine object is associated with an exo, and reads/stores exo data, applies logic to
        determine gait states and phases, chooses the correct controllers, and applies the
        controller.'''
        self.control_state = None
        self.controller_used = None
        self.muscle_model_update = None
        self.exo = exo
        self.stance_controller = stance_controller
        self.swing_controller = swing_controller
        self.reel_out_controller = reel_out_controller
        self.reel_in_controller = reel_in_controller
        self.controller_now = self.reel_out_controller
        self.just_starting = True
        self.swing_only = swing_only
        self.reel_in_controller_used, self.swing_controller_used, self.reel_out_controller_used, self.stance_controller_used = \
            reel_in_controller_used, swing_controller_used, reel_out_controller_used, stance_controller_used
        self.config = config

    def step(self, read_only=False):
        # Check state machine transition criteria, switching controller_now if criteria are met
        if self.just_starting:
            self.controller_now = self.reel_out_controller
            self.just_starting = False
            did_controllers_switch = True
            self.control_state = constants.ControlState.ReelOutState.value
            self.controller_used = self.reel_out_controller_used
        elif self.swing_only:  # for swing only
            self.controller_now = self.swing_controller
            did_controllers_switch = True  # update gains every time for now
            self.controller_used = self.swing_controller_used
            self.control_state = constants.ControlState.SwingState.value
        elif (self.controller_now == self.swing_controller and
              self.exo.data.did_heel_strike and
                self.exo.data.gait_phase is not None):
            self.controller_now = self.reel_in_controller
            did_controllers_switch = True
            self.exo.data.gen_var1 = 0
            self.controller_used = self.reel_in_controller_used
            self.control_state = constants.ControlState.ReelInState.value
        elif self.controller_now == self.reel_in_controller and self.reel_in_controller.check_completion_status():
            self.controller_now = self.stance_controller
            did_controllers_switch = True
            self.exo.data.gen_var1 = 1
            
            self.controller_used = self.stance_controller_used
            self.control_state = constants.ControlState.StanceState.value
        elif self.controller_now == self.stance_controller and (self.exo.data.did_toe_off or self.exo.data.gait_phase is None):
            self.controller_now = self.reel_out_controller
            did_controllers_switch = True
            self.exo.data.gen_var1 = 2
            self.controller_used = self.reel_out_controller_used
            self.control_state = constants.ControlState.ReelOutState.value
        elif self.controller_now == self.reel_out_controller and self.reel_out_controller.check_completion_status():
            self.controller_now = self.swing_controller
            did_controllers_switch = True
            self.exo.data.gen_var1 = 3
            self.controller_used = self.swing_controller_used
            self.control_state = constants.ControlState.SwingState.value
        else:
            did_controllers_switch = False

        self.exo.data.controller = self.controller_used
        self.exo.data.control_state = self.control_state

        if not read_only:
            self.controller_now.command(reset=did_controllers_switch)

            if self.config.STANCE_CONTROL_STYLE == config_util.StanceCtrlStyle.VIRTUALNEUROMUSCULARCONTROLLER and self.exo.data.controller != constants.ControllerUsed.VirtualNeuromusuclarController.value:
                self.muscle_model_update = self.stance_controller
                self.muscle_model_update.update_muscle_model(m_stim=0.01, phi0=self.exo.data.ankle_angle)

    def update_ctrl_params_from_config(self, config):
        self.stance_controller.update_ctrl_params_from_config(config=config)
        if self.swing_only != config.SWING_ONLY:
            self.swing_only = config.SWING_ONLY
            print('Updated swing only to: ', self.swing_only)

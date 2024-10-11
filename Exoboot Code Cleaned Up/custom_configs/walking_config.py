import config_util
config = config_util.ConfigurableConstants()
config.TASK = config_util.Task.WALKING

config.TARGET_FREQ = 175
config.STANCE_CONTROL_STYLE = config_util.StanceCtrlStyle.VIRTUALNEUROMUSCULARCONTROLLER
config.SCALING_FACTOR = 1.6
config.VNMC_GAIN = 2.4
config.MUSCLE_UPDATE_FREQUENCY = 1
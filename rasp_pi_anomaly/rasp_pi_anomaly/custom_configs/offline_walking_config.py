import config_util
from config_util import ConfigurableConstants

config = ConfigurableConstants()
config.IS_HARDWARE_CONNECTED = False
config.mode = "offline"  # Ensure this is set for offline testing
config.TASK = config_util.Task.WALKING
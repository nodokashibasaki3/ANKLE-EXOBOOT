import config_util
from config_util import ConfigurableConstants
config = ConfigurableConstants()

#basic settings for online
config.IS_HARDWARE_CONNECTED = True
config.mode = "online"
config.TASK = config_util.Task.WALKING
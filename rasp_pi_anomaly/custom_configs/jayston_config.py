import config_util
config = config_util.ConfigurableConstants()
# config.READ_ONLY = False
# config.DO_READ_FSRS = True
# config.SPLINE_BIAS = 3

# # Max's Values
# config.RISE_FRACTION: float = 0.2
# config.PEAK_FRACTION: float = 0.53
# config.FALL_FRACTION: float = 0.63
# config.PEAK_TORQUE: float = 20

# Optimized Values
config.RISE_FRACTION = 0.278
config.PEAK_FRACTION = 0.543
config.FALL_FRACTION = 0.641
config.PEAK_TORQUE = 25

# Generic Values
# config.RISE_FRACTION: float = 0.262
# config.PEAK_FRACTION: float = 0.529
# config.FALL_FRACTION: float = 0.627
# config.PEAK_TORQUE: float = 25

''' Here are the variables that are updatable in config, and their defaults:

    TARGET_FREQ: float = 200  # Hz
    ACTPACK_FREQ: float = 200  # Hz
    DO_DEPHY_LOG: bool = True
    DEPHY_LOG_LEVEL: int = 4
    TASK: Type[Task] = Task.WALKING
    STANCE_CONTROL_STYLE: Type[StanceCtrlStyle] = StanceCtrlStyle.FOURPOINTSPLINE
    MAX_ALLOWABLE_CURRENT = 20000  # mA

    # Gait State details
    HS_GYRO_THRESHOLD: float = 100
    HS_GYRO_FILTER_N: int = 2
    HS_GYRO_FILTER_WN: float = 3
    HS_GYRO_DELAY: float = 0.05
    SWING_SLACK: int = 10000
    TOE_OFF_FRACTION: float = 0.62
    REEL_IN_TIMEOUT: float = 0.2

    # 4 point Spline
    RISE_FRACTION: float = 0.2
    PEAK_FRACTION: float = 0.53
    FALL_FRACTION: float = 0.63
    PEAK_TORQUE: float = 5
    SPLINE_BIAS: float = 3  # Nm

    # Impedance
    K_VAL: int = 500
    B_VAL: int = 0
    SET_POINT: float = 0  # Deg

    READ_ONLY = False  # Does not require Lipos
    DO_READ_FSRS = False

    PRINT_HS = True  # Print heel strikes
    SLIP_DETECT_ACTIVE = False
'''

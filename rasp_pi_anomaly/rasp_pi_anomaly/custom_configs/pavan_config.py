
import config_util
config = config_util.ConfigurableConstants()

config.TASK = config_util.Task.ANOMALY
config.READ_ONLY = False
# peak_fraction_from_training = 0.63
# config.RISE_FRACTION = 0.2*(1/peak_fraction_from_training)
# config.PEAK_FRACTION = 0.53*(1/peak_fraction_from_training)
# config.FALL_FRACTION = 0.9  #check this value
# config.PEAK_TORQUE = 5
config.RISE_FRACTION = 0.2
config.PEAK_FRACTION = 0.53
config.FALL_FRACTION = 0.60
config.PEAK_TORQUE = 25
config.SPLINE_BIAS = 3  # Nm

config.SWING_ONLY = True
config.DO_INCLUDE_GEN_VARS = True
config.TARGET_FREQ = 175
config.DO_READ_SYNC = False

# config.DO_FILTER_GAIT_PHASE = True


''' Here are the variables that are updatable in config, and their defaults:

    TARGET_FREQ: float = 175  # Hz
    ACTPACK_FREQ: float = 200  # Hz
    DO_DEPHY_LOG: bool = False
    DEPHY_LOG_LEVEL: int = 4
    ONLY_LOG_IF_NEW: bool = True

    TASK: Type[Task] = Task.WALKING
    STANCE_CONTROL_STYLE: Type[StanceCtrlStyle] = StanceCtrlStyle.FOURPOINTSPLINE
    MAX_ALLOWABLE_CURRENT = 20000  # mA

    # Gait State details
    HS_GYRO_THRESHOLD: float = 100
    HS_GYRO_FILTER_N: int = 2
    HS_GYRO_FILTER_WN: float = 3
    HS_GYRO_DELAY: float = 0.05
    SWING_SLACK: int = 10000
    TOE_OFF_FRACTION: float = 0.60
    REEL_IN_MV: int = 1200
    REEL_IN_SLACK_CUTOFF: int = 1200
    REEL_IN_TIMEOUT: float = 0.2
    NUM_STRIDES_REQUIRED: int = 2
    SWING_ONLY: bool = False

    # 4 point Spline
    RISE_FRACTION: float = 0.2
    PEAK_FRACTION: float = 0.53
    FALL_FRACTION: float = 0.60
    PEAK_TORQUE: float = 5
    SPLINE_BIAS: float = 3  # Nm

    # Impedance
    K_VAL: int = 500
    B_VAL: int = 0
    B_RATIO: float = 0.5  # when B_VAL is a function of B_RATIO. 2.5 is approx. crit. damped
    SET_POINT: float = 0  # Deg

    READ_ONLY: bool = False  # Does not require Lipos
    DO_READ_FSRS: bool = False
    DO_READ_SYNC: bool = False

    PRINT_HS: bool = True  # Print heel strikes
    VARS_TO_PLOT: List = field(default_factory=lambda: [])
    DO_DETECT_SLIP: bool = False
    SLIP_DETECT_ACTIVE: bool = False
    DO_INCLUDE_GEN_VARS: bool = False
    SLIP_DETECT_DELAY: int = 0
    DO_FILTER_GAIT_PHASE: bool = False
    EXPERIMENTER_NOTES: str = 'Experimenter notes go here'
'''

import os.path

# working directory for daemon logs and persistance files
DIR = '/home/pi/.encoderd/'

# stores current system pid
PID_FILE=os.path.join(DIR,'encoderd.pid')

# log file
LOG_FILE=os.path.join(DIR,'encoderd.log')

# refresh rate (time in seconds between angle checks for display)
REFRESH_RATE = 0.1

# Precision de lecture en degres
PRECISION = 3

# list of attached encoders
ENCODERS=[
  dict(
    name="HN3806A",                # device nickname
    pinA=17,                     # BCM number
    pinB=18,                     # BCM pin number
    calibration=360/600, # degrees/step, HN3806-AB-600N
    logfile=os.path.join(DIR,"Angle_HN3806A.log"),   # stores last known encoder value
  ),
  dict(
    name="HN3806B",                # device nickname
    pinA=23,                     # BCM pin number
    pinB=24,                     # BCM pin number
    calibration=360/600, # degrees/step, HN3806-AB-600N
    logfile=os.path.join(DIR,"Angle_HN3806B.log"),   # stores last known encoder value
  ),
  dict(
    name="LPD3806",                # device nickname
    pinA=20,                     # BCM pin number
    pinB=21,                     # BCM pin number
    calibration=360/400, # degrees/step, LPD3806-400BM-G5-24C
    logfile=os.path.join(DIR,"Angle_LPD3806.log"),   # stores last known encoder value
  ),
]

# create directory if it doesn't exist
if not os.path.exists(DIR):
  print("logging directory not found, attempting to create")
  os.makedirs(DIR)
  print("logging directory created: %s", DIR)

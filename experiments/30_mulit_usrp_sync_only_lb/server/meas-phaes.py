import time # std module
import pyvisa as visa # http://github.com/hgrecco/pyvisa
import numpy as np # http://www.numpy.org/
from scipy.signal import find_peaks

from enum import Enum

import matplotlib.pyplot as plt

ip = "192.108.1.219"

rm = visa.ResourceManager()
scope = rm.open_resource(f'TCPIP::{ip}::INSTR')

# scope.write('*rst') # reset

# Query list of measurements
# meas_list = scope.query("MEASUrement:LIST?")
# meas_list = meas_list.replace('\n', '').split(',')

# Define channels (phase measurment)
channel_1 = "CH1"
channel_2 = "CH2"
channel_3 = "CH3"
channel_4 = "CH4"

channels = [channel_1, channel_2, channel_3, channel_4]

for i in range(4):
  scope.write(f"{channels[i]}:TERMINATION 50")
  scope.write(f"{channels[i]}:BANdwidth 2e9")
  scope.write(f"SELECT:{channels[i]} 1")

scope.write("HORIZONTAL:MODE:SCALE 400e-12")
scope.write("DISplay:WAVEView1:VIEWStyle OVERLAY")

voltages = {}

for i in range(4):
  scope.write(f"DATA:SOURCE {channels[i]}")
  scope.write("DATA:START 1")
  scope.write("DATA:STOP 1000")
  ymult = float(scope.query(":WFMOutpre:YMULT?"))   # volts per bit
  yoff  = float(scope.query(":WFMOutpre:YOFF?"))    # offset in bits
  yzero = float(scope.query(":WFMOutpre:YZERO?"))   # referentie (meestal 0)
  raw = scope.query_binary_values("CURVe?", datatype="b", container=np.array)
  volt = (raw - yoff) * ymult + yzero

  voltages[f"{channels[i]}"] = volt


phase_diff_deg = {}
for ch in channels[1:]:
    V1_fft = np.fft.fft(voltages['CH1'])
    Vx_fft = np.fft.fft(voltages[f'{ch}'])
    
    # Vind dominante frequentie (max amplitude in FFT)
    k = np.argmax(np.abs(V1_fft))
    
    # Bereken faseverschil in graden
    phase_diff = np.angle(Vx_fft[k]) - np.angle(V1_fft[k])
    phase_diff_deg[f'CH{ch}_rel_CH1'] = np.degrees(phase_diff)


for ch, phase in phase_diff_deg.items():
    print(f"{ch}: {phase:.2f}°")


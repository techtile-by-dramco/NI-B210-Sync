import pyvisa as visa
import numpy as np

class Scope:
    def __init__(self, ip, sample_start=1, sample_stop=1000):
        self.ip = ip
        self.rm = visa.ResourceManager()
        self.scope = self.rm.open_resource(f'TCPIP::{self.ip}::INSTR')
        
        self.channels = ["CH1", "CH2", "CH3", "CH4"]
        self.sample_start = sample_start
        self.sample_stop = sample_stop
        self.voltages = {}
        self.phase_diff_deg = {}

    def setup_channels(self):
        for ch in self.channels:
            self.scope.write(f"{ch}:TERMINATION 50")
            self.scope.write(f"{ch}:BANdwidth 2e9")
            self.scope.write(f"SELECT:{ch} 1")

        self.scope.write("HORIZONTAL:MODE:SCALE 400e-12")
        self.scope.write("DISplay:WAVEView1:VIEWStyle OVERLAY")

    def read_waveforms(self):
        for ch in self.channels:
            self.scope.write(f"DATA:SOURCE {ch}")
            self.scope.write(f"DATA:START {self.sample_start}")
            self.scope.write(f"DATA:STOP {self.sample_stop}")

            ymult = float(self.scope.query(":WFMOutpre:YMULT?"))
            yoff  = float(self.scope.query(":WFMOutpre:YOFF?"))
            yzero = float(self.scope.query(":WFMOutpre:YZERO?"))

            raw = self.scope.query_binary_values("CURVe?", datatype="b", container=np.array)
            volt = (raw - yoff) * ymult + yzero
            self.voltages[ch] = volt

    def calculate_phase_diff(self):
        V1_fft = np.fft.fft(self.voltages['CH1'])
        for ch in self.channels[1:]:
            Vx_fft = np.fft.fft(self.voltages[ch])
            k = np.argmax(np.abs(V1_fft))
            phase_diff = np.angle(Vx_fft[k]) - np.angle(V1_fft[k])
            self.phase_diff_deg[f'{ch}_rel_CH1'] = np.degrees(phase_diff)

    def get_phase_diff(self, channel):
        key = f'{channel}_rel_CH1'
        return self.phase_diff_deg.get(key, None)



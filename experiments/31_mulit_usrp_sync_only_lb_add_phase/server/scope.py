# import pyvisa as visa
# import numpy as np

# class Scope:
#     def __init__(self, ip, sample_start=1, sample_stop=1000):
#         self.ip = ip
#         self.rm = visa.ResourceManager()
#         self.scope = self.rm.open_resource(f'TCPIP::{self.ip}::INSTR')
        
#         self.channels = ["CH1", "CH2", "CH3", "CH4"]
#         self.sample_start = sample_start
#         self.sample_stop = sample_stop
#         self.voltages = {}
#         self.phase_diff_deg = {}

#     def setup_channels(self):
#         for ch in self.channels:
#             self.scope.write(f"{ch}:TERMINATION 50")
#             self.scope.write(f"{ch}:BANdwidth 2e9")
#             self.scope.write(f"SELECT:{ch} 1")

#         self.scope.write("HORIZONTAL:MODE:SCALE 400e-12")
#         self.scope.write("DISplay:WAVEView1:VIEWStyle OVERLAY")

#     def read_waveforms(self):
#         for ch in self.channels:
#             self.scope.write(f"DATA:SOURCE {ch}")
#             self.scope.write(f"DATA:START {self.sample_start}")
#             self.scope.write(f"DATA:STOP {self.sample_stop}")

#             ymult = float(self.scope.query(":WFMOutpre:YMULT?"))
#             yoff  = float(self.scope.query(":WFMOutpre:YOFF?"))
#             yzero = float(self.scope.query(":WFMOutpre:YZERO?"))

#             raw = self.scope.query_binary_values("CURVe?", datatype="b", container=np.array)
#             volt = (raw - yoff) * ymult + yzero
#             self.voltages[ch] = volt

#     def calculate_phase_diff(self):
#         V1_fft = np.fft.fft(self.voltages['CH1'])
#         for ch in self.channels[1:]:
#             Vx_fft = np.fft.fft(self.voltages[ch])
#             k = np.argmax(np.abs(V1_fft))
#             phase_diff = np.angle(Vx_fft[k]) - np.angle(V1_fft[k])
#             self.phase_diff_deg[f'{ch}_rel_CH1'] = np.degrees(phase_diff)

#     def get_phase_diff(self, channel):
#         key = f'{channel}_rel_CH1'
#         return self.phase_diff_deg.get(key, None)



import time
import pyvisa as visa
import numpy as np
from scipy.signal import find_peaks


class Scope:
    def __init__(self, ip: str):
        self.ip = ip
        self.rm = visa.ResourceManager()
        self.scope = self.rm.open_resource(f"TCPIP::{ip}::INSTR")
        self.channels = ["CH1", "CH2", "CH3", "CH4"]


    # ------------------------------------------------------------
    # BASIC INITIALIZATION
    # ------------------------------------------------------------
    def _init_scope(self):
        """Reset scope and configure channels."""
        print("[i] Resetting scope…")
        self.scope.write("*rst")

        # Add 3 phase measurements
        print("[i] Adding phase measurements…")
        for _ in range(3):
            self.scope.write("MEASUREMENT:ADDMEAS PHASE")

        # Get measurement names
        self.meas_list = self.scope.query("MEASUrement:LIST?").strip().split(",")

        # Configure channels
        print("[i] Configuring channels…")
        for ch in self.channels:
            self.scope.write(f"{ch}:TERMINATION 50")
            self.scope.write(f"{ch}:BANdwidth 2e9")
            self.scope.write(f"SELECT:{ch} 1")

        # Horizontal scale, overlay view
        self.scope.write("HORIZONTAL:MODE:SCALE 400e-12")
        self.scope.write("DISplay:WAVEView1:VIEWStyle OVERLAY")

        # Link measurements to channels
        print("[i] Mapping measurement sources…")
        for i in range(3):
            self.scope.write(f"MEASUrement:{self.meas_list[i]}:SOUrce1 CH1")
            self.scope.write(f"MEASUrement:{self.meas_list[i]}:SOUrce2 {self.channels[i+1]}")
    
    def check_status(self):
        no_meas = len(self.scope.query("MEASUrement:LIST?").strip().split(","))
        if(no_meas != 3):
            return True
        return False

    # ------------------------------------------------------------
    # READOUT
    # ------------------------------------------------------------
    def read_measurements(self):
        """Read the mean history value for all configured measurements."""
        measurements = self.scope.query("MEASUrement:LIST?").strip().split(",")
        results = {}

        for meas in measurements:
            value = self.scope.query(f"MEASUrement:{meas}:RESUlts:HISTory:MEAN?")
            results[meas] = float(value)
        return results

    # # ------------------------------------------------------------
    # # LOOP
    # # ------------------------------------------------------------
    # def run(self, interval: float = 1.0):
    #     """Continuously print measurement results."""
    #     print("[i] Starting measurement loop…")

    #     while True:
    #         data = self.read_measurements()

    #         for meas, val in data.items():
    #             print(f"{meas}: {val:.6e}", end="  ")

    #         print()
    #         time.sleep(interval)

    # ------------------------------------------------------------
    # CLEANUP
    # ------------------------------------------------------------
    def close(self):
        """Close VISA session."""
        self.scope.close()
        self.rm.close()
        print("[i] VISA session closed.")


# ------------------------------------------------------------
# USAGE
# ------------------------------------------------------------
if __name__ == "__main__":
    scope = Scope(ip="192.108.1.219")
    # try:
    #     scope.run(interval=1)
    # except KeyboardInterrupt:
    #     scope.close()

    if scope.check_status():
        scope._init_scope()
    else:
        print("Scope setup already ok!")

    data = scope.read_measurements()
    print(data)


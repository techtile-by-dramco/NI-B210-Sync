import os
import csv
from datetime import datetime
from scope import Scope  # jouw class

def save_phases():
    # === Maak Scope object aan en lees data ===
    scope_obj = Scope("192.108.1.219")
    scope_obj.setup_channels()
    scope_obj.read_waveforms()
    scope_obj.calculate_phase_diff()

    # === Verkrijg fasen ===
    ch2_phase = scope_obj.get_phase_diff("CH2")
    ch3_phase = scope_obj.get_phase_diff("CH3")
    ch4_phase = scope_obj.get_phase_diff("CH4")

    # === Huidig pad opvragen en één niveau hoger ===
    current_file_path = os.path.abspath(__file__) 
    current_dir = os.path.dirname(current_file_path)
    parent_path = os.path.dirname(current_dir)
    data_folder = os.path.join(parent_path, "data")

    # === Zorg dat de folder bestaat ===
    os.makedirs(data_folder, exist_ok=True)

    # === CSV-bestand met timestamp in de naam ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = os.path.join(data_folder, f"results.csv")

    # === Schrijf data naar CSV ===
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["ts", "CH2", "CH3", "CH4"])  # header
        writer.writerow([timestamp, ch2_phase, ch3_phase, ch4_phase])

    print(f"Data opgeslagen in {csv_file}")

    scope_obj.scope.close()

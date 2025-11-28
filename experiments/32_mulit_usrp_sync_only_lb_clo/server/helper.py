import os
import csv
from datetime import datetime
from scope import Scope  # jouw class

def save_phases():
    # === Maak Scope object aan en lees data ===
    scope_obj = Scope(ip="192.108.1.219")

    # === Initialize scope
    if scope_obj.check_status():
        scope_obj._init_scope()
    else:
        print("Scope setup already ok!")

    # === Get data
    data = scope_obj.read_measurements()

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
        writer.writerow([timestamp, data["MEAS1"], data["MEAS2"], data["MEAS3"]])

    print(f"Data opgeslagen in {csv_file}")

    scope_obj.scope.close()

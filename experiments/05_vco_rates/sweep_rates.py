import os
import re
import time
import uhd
import pandas as pd

# -----------------------------------------------------------------------------
# 🔧 Logging Setup
# -----------------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "uhd_debug_trace.log")
csv_path = os.path.join(script_dir, "clock_tuning_summary.csv")

os.environ["UHD_LOG"] = "trace,all"
os.environ["UHD_LOG_FILE_LEVEL"] = "trace"
os.environ["UHD_LOG_FILE"] = log_path
os.environ["UHD_LOG_OPTIONS"] = f"file={log_path}"

# -----------------------------------------------------------------------------
# 🎯 Master clock rates to test (≤ 61 MHz, valid for B210)
# -----------------------------------------------------------------------------
MASTER_CLOCK_RATES = [
    rate for rate in [
        4e6, 8e6, 10e6, 12.5e6, 16e6, 20e6, 25e6, 32e6, 40e6, 50e6, 61e6
    ]
]

# -----------------------------------------------------------------------------
# 📊 Log parsing patterns
# -----------------------------------------------------------------------------
patterns = {
    "rate": re.compile(r"_tune_bbvco\] rate=([0-9.e+]+)"),
    "vcorate": re.compile(r"actual vcorate=([0-9.e+]+)"),
    "vcodiv": re.compile(r"vcodiv=([0-9]+) vcorate=([0-9.e+]+)"),
    "nint": re.compile(r"nint=([0-9]+) nfrac=([0-9]+)"),
    "divfactor": re.compile(r"_setup_rates\] divfactor=([0-9]+)"),
    "adcclk": re.compile(r"adcclk=([0-9.e+]+)"),
}

# -----------------------------------------------------------------------------
# 🧠 Extract tuning parameters from a block of log lines
# -----------------------------------------------------------------------------
def parse_one_run(lines, master_clock_rate):
    values = {
        "master_clock_rate": master_clock_rate,
        "rate": None,
        "divfactor": None,
        "vcorate": None,
        "vcodiv": None,
        "nint": None,
        "nfrac": None,
        "adcclk": None
    }

    for line in lines:
        for key, pattern in patterns.items():
            match = pattern.search(line)
            if match:
                if key == "vcodiv":
                    values["vcodiv"] = int(match.group(1))
                elif key == "nint":
                    values["nint"] = int(match.group(1))
                    values["nfrac"] = int(match.group(2))
                else:
                    values[key] = float(match.group(1))
    return values

# -----------------------------------------------------------------------------
# 🧹 Group the log by clock rate transitions and parse each section
# -----------------------------------------------------------------------------
def extract_trace_data(log_file):
    results = []
    current_rate = None
    trace_buffer = []

    with open(log_file, "r") as f:
        for line in f:
            match = re.search(r"B200,Asking for clock rate ([0-9.]+) MHz", line)
            if match:
                if current_rate is not None and trace_buffer:
                    results.append(parse_one_run(trace_buffer, current_rate))
                    trace_buffer = []

                current_rate = float(match.group(1)) * 1e6  # MHz → Hz
                continue

            if current_rate is not None:
                trace_buffer.append(line)

    # Final segment
    if current_rate is not None and trace_buffer:
        results.append(parse_one_run(trace_buffer, current_rate))

    return results

# -----------------------------------------------------------------------------
# 🚀 Main sweep logic
# -----------------------------------------------------------------------------
def main():
    print("📡 Starting master clock sweep...")

    if os.path.exists(log_path):
        os.remove(log_path)

    for rate in MASTER_CLOCK_RATES:
        print(f"🔁 Testing {rate/1e6:.1f} MHz")
        try:
            usrp = uhd.usrp.MultiUSRP()
            usrp.set_master_clock_rate(rate)
            usrp.set_rx_freq(917e6)
            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ Error with {rate/1e6:.1f} MHz: {e}")

    print("\n📄 Parsing UHD trace log...")
    results = extract_trace_data(log_path)

    if not results:
        print("❌ No tuning blocks were extracted. Check if UHD emitted the expected lines.")
        return

    df = pd.DataFrame(results)
    print("\n✅ Sweep complete. Summary:")
    print(df.to_string(index=False))

    df.to_csv(csv_path, index=False)
    print(f"\n📁 Results saved to: {csv_path}")
    print(f"🪵 Raw trace log: {log_path}")

if __name__ == "__main__":
    main()

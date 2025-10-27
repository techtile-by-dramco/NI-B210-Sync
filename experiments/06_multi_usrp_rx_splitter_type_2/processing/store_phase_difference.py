import numpy as np
import os
import matplotlib.pyplot as plt
import yaml
import argparse
import scipy.signal as signal
from scipy.stats import circmean, circstd
from collections import defaultdict
from matplotlib.patches import Wedge
from matplotlib.colors import Normalize
import csv
import re

# Function to apply a bandpass filter to the IQ data
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = signal.butter(order, [low, high], btype='band', output='sos')
    return sos

# Function to apply the bandpass filter
def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    sos = butter_bandpass(lowcut, highcut, fs, order)
    return signal.sosfilt(sos, data)

# Function to load metadata from YML file
def load_metadata_from_yml(filename):
    # The metadata file should have the same name, except for the prefix "data_" being replaced with "metadata_"
    yml_file = filename.replace('data_', 'metadata_').replace('.npy', '.yml')
    if os.path.exists(yml_file):
        with open(yml_file, 'r') as f:
            metadata = yaml.safe_load(f)
        return metadata
    else:
        print(f"Metadata file {yml_file} not found!")
        return None

# Function to load phase difference data from .npy file
def load_iq_data(filename):
    return np.load(filename)

# Function to compute phase difference between two channels
def compute_phase_difference(iq_data, fs):
    # Define fixed parameters for filter
    f0 = 1e3  # Center frequency for bandpass filter (Hz)
    cutoff = 250  # Cutoff range for bandpass filter (Hz)
    lowcut = f0 - cutoff
    highcut = f0 + cutoff

    # Apply bandpass filter to the real and imaginary parts
    iq_filtered = butter_bandpass_filter(iq_data, lowcut, highcut, fs)
    
    # Calculate the phase of the filtered IQ data
    phase = np.angle(iq_filtered)
    
    # Calculate the phase difference between channels A and B (CH0 and CH1)
    phase_diff = np.unwrap(phase[0, :]) - np.unwrap(phase[1, :])
    
    # # Ensure that phase difference values close to -pi and pi are wrapped correctly
    # phase_diff = np.mod(phase_diff + np.pi, 2 * np.pi) - np.pi  # This ensures phase is wrapped between -pi and pi

    return phase_diff

def extract_hostname_from_filename(filename):
    import re
    match = re.search(r"data_(t\d{2})_", filename, re.IGNORECASE)
    return match.group(1).upper() if match else None

# Function to plot phase difference vs RX gain B as a banded circular plot
def store_phase_difference(in_dir, out_dir):
    phase_differences = defaultdict(list)
    amplitude_max_i = defaultdict()
    amplitude_max_q = defaultdict()
    gain_b_values = []
    gain_a_values = []

    # Default tile name variable
    tile_name = "A00"
    
    # Loop through the files in the directory
    for filename in os.listdir(in_dir):
        if filename.endswith(".npy"):
            
            # Search for tile name
            match = re.search(r'_([A-Za-z]\d{2})_', filename)
            if match:
                tile_name = match.group(0).strip('_')

            # Load phase difference data
            iq_data = load_iq_data(os.path.join(in_dir, filename))
            
            # Load metadata from the corresponding YML file
            metadata = load_metadata_from_yml(os.path.join(in_dir, filename))

            if metadata is None:
                continue
            
            # Extract RX gain B from metadata
            gain_a = int(metadata['rx_gain_a'])
            gain_b = int(metadata['rx_gain_b'])

            if "hostname" in metadata:
                hostname = metadata['hostname']
            else:
                hostname = extract_hostname_from_filename(filename)
            
            if hostname is None:
                ValueError("no hostname found")

            gain_a_values.append(gain_a)
            gain_b_values.append(gain_b)

            fs = metadata['sampling_rate']
            
            # Compute the phase difference for the file
            phase_diff = compute_phase_difference(iq_data, fs)

            i_vals = np.real(iq_data)
            q_vals = np.imag(iq_data)
            max_i = np.max(np.abs(i_vals))
            max_q = np.max(np.abs(q_vals))
            
            # Append the phase difference for this RX gain B
            phase_differences[(hostname, gain_a, gain_b)].extend(phase_diff)
            amplitude_max_i[(hostname, gain_a, gain_b)] = max_i
            amplitude_max_q[(hostname, gain_a, gain_b)] = max_q
            print(f"{hostname} {gain_a}dB {gain_b}dB {np.rad2deg(circmean(phase_diff)):.2f}° {np.rad2deg(circstd(phase_diff)):.2f}°")

    # Prepare CSV file to store the circmean and circstd for each gain value
    csv_filename = os.path.join(out_dir, f"{tile_name}_circmean_and_circstd.csv")
    with open(csv_filename, mode='w', newline='') as csvfile:
        fieldnames = ['hostname','RX Gain A','RX Gain B', 'Circular Mean (degrees)', 'Circular Std Dev (degrees)', 'max_i', 'max_q']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        # Add wedges for each phase difference and gain
        for (hostname, gain_a, gain_b), phase_rad in phase_differences.items():

            # Compute circmean and circstd for the current RX gain B
            circ_mean = circmean(phase_rad, high=np.pi, low=-np.pi)  # Circular mean in radians
            circ_var = circstd(phase_rad, high=np.pi, low=-np.pi) ** 2  # Circular variance
            circ_mean_deg = np.rad2deg(circ_mean)  # Convert to degrees
            circ_var_deg = np.rad2deg(np.sqrt(circ_var))  # Convert variance to standard deviation (in degrees)

            # Write to CSV file
            writer.writerow({'hostname': hostname,
                             'RX Gain A': gain_a, 
                             'RX Gain B': gain_b, 
                             'Circular Mean (degrees)': circ_mean_deg, 
                             'Circular Std Dev (degrees)': circ_var_deg,
                             'max_i':amplitude_max_i[(hostname, gain_a, gain_b)],
                             'max_q':amplitude_max_q[(hostname, gain_a, gain_b)]})
        
        print(f"Circular mean and std dev saved as {csv_filename}")

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", type=str, default='./data/', help="Directory containing IQ data files and metadata (default: current directory)")
    parser.add_argument("--out-dir", type=str, default='./results/', help="Directory output")
    args = parser.parse_args()
    
    # Plot phase difference vs RX gain B with circular variance
    store_phase_difference(args.in_dir, args.out_dir)

if __name__ == "__main__":
    main()

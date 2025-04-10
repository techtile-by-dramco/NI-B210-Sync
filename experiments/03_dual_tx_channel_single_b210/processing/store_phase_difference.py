import numpy as np
import os
import matplotlib.pyplot as plt
import yaml
import argparse
import scipy.signal as signal
from scipy.stats import circmean, circstd
from collections import defaultdict
import csv

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
def load_phase_difference(filename):
    return np.load(filename)

# Function to compute phase difference between two channels
def compute_phase_difference(iq_data, fs):
    # Define fixed parameters for filter
    f0 = 1e3  # Center frequency for bandpass filter (Hz)
    cutoff = 100  # Cutoff range for bandpass filter (Hz)
    lowcut = f0 - cutoff
    highcut = f0 + cutoff

    # Apply bandpass filter to the real and imaginary parts
    iq_filtered = butter_bandpass_filter(iq_data, lowcut, highcut, fs)
    
    # Calculate the phase of the filtered IQ data
    phase = np.angle(iq_filtered)
    
    # Calculate the phase difference between channels A and B (CH0 and CH1)
    phase_diff = np.unwrap(phase[0, :]) - np.unwrap(phase[1, :])
    
    # Ensure that phase difference values close to -pi and pi are wrapped correctly
    phase_diff = np.mod(phase_diff + np.pi, 2 * np.pi) - np.pi  # This ensures phase is wrapped between -pi and pi

    return phase_diff

# Function to store phase difference data with TX gain B
def store_phase_difference(in_dir, out_dir, fs):
    phase_differences_by_tx_gain_b = defaultdict(list)
    tx_gain_b_values = []
    
    # Loop through the files in the directory
    for filename in os.listdir(in_dir):
        if filename.endswith(".npy"):
            # Load phase difference data
            iq_data = load_phase_difference(os.path.join(in_dir, filename))
            
            # Load metadata from the corresponding YML file
            metadata = load_metadata_from_yml(os.path.join(in_dir, filename))

            if metadata is None:
                continue
            
            # Extract TX gain B from metadata
            tx_gain_b = metadata['tx_gain_b']
            tx_gain_b_values.append(tx_gain_b)
            
            # Compute the phase difference for the file
            phase_diff = compute_phase_difference(iq_data, fs)
            
            # Append the phase difference for this TX gain B
            phase_differences_by_tx_gain_b[tx_gain_b].extend(phase_diff)

    # Prepare CSV file to store the circmean and circstd for each TX gain B value
    csv_filename = os.path.join(out_dir, "circmean_and_circstd.csv")
    with open(csv_filename, mode='w', newline='') as csvfile:
        fieldnames = ['TX Gain B', 'Circular Mean (degrees)', 'Circular Std Dev (degrees)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        # Add data for each phase difference and TX gain B
        for gain, phase_rad in phase_differences_by_tx_gain_b.items():

            # Compute circmean and circstd for the current TX gain B
            circ_mean = circmean(phase_rad, high=np.pi, low=-np.pi)  # Circular mean in radians
            circ_var = circstd(phase_rad, high=np.pi, low=-np.pi) ** 2  # Circular variance
            circ_mean_deg = np.rad2deg(circ_mean)  # Convert to degrees
            circ_var_deg = np.rad2deg(np.sqrt(circ_var))  # Convert variance to standard deviation (in degrees)

            # Write to CSV file
            writer.writerow({'TX Gain B': gain, 'Circular Mean (degrees)': circ_mean_deg, 'Circular Std Dev (degrees)': circ_var_deg})
        
        print(f"Circular mean and std dev saved as {csv_filename}")

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", type=str, default='./data/', help="Directory containing IQ data files and metadata (default: current directory)")
    parser.add_argument("--out-dir", type=str, default='./results/', help="Directory output")
    parser.add_argument("--fs", type=int, default=250000, help="Sampling frequency (Hz)")
    args = parser.parse_args()
    
    # Store phase difference data with TX gain B from metadata
    store_phase_difference(args.in_dir, args.out_dir, args.fs)

if __name__ == "__main__":
    main()

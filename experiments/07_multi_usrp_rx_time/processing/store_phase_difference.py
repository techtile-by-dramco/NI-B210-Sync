import numpy as np
import os
import matplotlib.pyplot as plt
import yaml
import argparse
import scipy.signal as signal
from scipy.stats import circmean, circstd
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
    yml_file = filename.replace('data_', 'metadata_').replace('.npy', '.yml')
    if os.path.exists(yml_file):
        with open(yml_file, 'r') as f:
            metadata = yaml.safe_load(f)
        return metadata
    else:
        print(f"Metadata file {yml_file} not found!")
        return None

# Function to load IQ data from .npy file
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

    return phase_diff

# Function to extract hostname from the filename (using regex)
def extract_hostname_from_filename(filename):
    match = re.search(r"data_(t\d{2})_", filename, re.IGNORECASE)
    return match.group(1).upper() if match else None

# Function to compute and store the phase difference mean and std per timestamp and hostname
def store_phase_difference(in_dir, out_dir):
    # Prepare CSV file to store the circmean and circstd for each gain value
    csv_filename = os.path.join(out_dir, "circmean_and_circstd_by_timestamp.csv")
    with open(csv_filename, mode='w', newline='') as csvfile:
        fieldnames = ['hostname', 'RX Gain A', 'RX Gain B', 'Timestamp', 'Circular Mean (degrees)', 'Circular Std Dev (degrees)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        # Loop through the files in the directory
        for filename in os.listdir(in_dir):
            if filename.endswith(".npy"):
                # Load IQ data
                iq_data = load_iq_data(os.path.join(in_dir, filename))
                
                # Load metadata from the corresponding YML file
                metadata = load_metadata_from_yml(os.path.join(in_dir, filename))

                if metadata is None:
                    continue
                
                # Extract RX gain A, RX gain B, and timestamp from metadata
                gain_a = int(metadata['rx_gain_a'])
                gain_b = int(metadata['rx_gain_b'])

                if "hostname" in metadata:
                    hostname = metadata['hostname']
                else:
                    hostname = extract_hostname_from_filename(filename)
                
                if hostname is None:
                    raise ValueError("No hostname found")

                fs = metadata['sampling_rate']
                timestamp = metadata['timestamp']
                
                # Compute the phase difference for the file
                phase_diff = compute_phase_difference(iq_data, fs)
                
                # Compute circular mean and std dev
                circ_mean = circmean(phase_diff, high=np.pi, low=-np.pi)  # Circular mean in radians
                circ_var = circstd(phase_diff, high=np.pi, low=-np.pi) ** 2  # Circular variance
                circ_mean_deg = np.rad2deg(circ_mean)  # Convert to degrees
                circ_var_deg = np.rad2deg(np.sqrt(circ_var))  # Convert variance to standard deviation (in degrees)

                # Write to CSV file
                writer.writerow({'hostname': hostname,
                                 'RX Gain A': gain_a, 
                                 'RX Gain B': gain_b, 
                                 'Timestamp': timestamp,
                                 'Circular Mean (degrees)': circ_mean_deg, 
                                 'Circular Std Dev (degrees)': circ_var_deg})

                print(f"{hostname} {gain_a}dB {gain_b}dB {timestamp} Phase Mean: {circ_mean_deg:.2f}° Phase Std: {circ_var_deg:.2f}°")

        print(f"Circular mean and std dev saved as {csv_filename}")

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", type=str, default='./data/', help="Directory containing IQ data files and metadata (default: current directory)")
    parser.add_argument("--out-dir", type=str, default='./results/', help="Directory to output CSV file")
    args = parser.parse_args()
    
    # Store phase difference per timestamp and hostname
    store_phase_difference(args.in_dir, args.out_dir)

if __name__ == "__main__":
    main()

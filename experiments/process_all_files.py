import numpy as np
import os
import matplotlib.pyplot as plt
import yaml
import argparse
import scipy.signal as signal
from scipy.stats import circmean, circstd
import xarray as xr
from collections import defaultdict

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

# Function to store IQ data in xarray and compute phase differences
def store_raw_iq_data_in_xarray():
    iq_data_all = []
    tx_gain_values_a = []
    tx_gain_values_b = []
    rx_gain_a_values = []
    rx_gain_b_values = []
    fs_values = []
    
    # Loop through the files in the directory recursively
    for root, dirs, files in os.walk(os.getcwd()):
        # Exclude the directory '01_dual_rx_channel_single_b210' from traversal
        if "01_dual_rx_channel_single_b210" in dirs:
            dirs.remove("01_dual_rx_channel_single_b210")  # This prevents os.walk from traversing this folder

        for filename in files:
            if filename.endswith(".npy"):
                # Load IQ data
                iq_data = load_iq_data(os.path.join(root, filename))
                
                # Load metadata from the corresponding YML file
                metadata = load_metadata_from_yml(os.path.join(root, filename))

                print(f"Processing: {os.path.join(root, filename)}",end="")

                if metadata is None:
                    continue
                
                # Extract TX Gain, RX Gain A, RX Gain B, and Sampling Rate from metadata
                if 'tx_gain' in metadata:  # If a single tx_gain is used for both TX channels
                    tx_gain_a = tx_gain_b = metadata['tx_gain']
                else:  # Separate values for TX Gain A and TX Gain B
                    tx_gain_a = metadata['tx_gain_a']
                    tx_gain_b = metadata['tx_gain_b']
                
                rx_gain_a = metadata['rx_gain_a']
                rx_gain_b = metadata['rx_gain_b']
                fs = metadata['sampling_rate']
                
                tx_gain_values_a.append(tx_gain_a)
                tx_gain_values_b.append(tx_gain_b)
                rx_gain_a_values.append(rx_gain_a)
                rx_gain_b_values.append(rx_gain_b)
                fs_values.append(fs)
                
                # Stack the IQ data (time, channel, sample)
                iq_data_all.append(iq_data)
                
                print("...Done.")
    
    print("Putting all in one netcdf file...",end="")
    # Convert the list of IQ data into a single numpy array (time, channel, sample)
    iq_data_combined = np.stack(iq_data_all, axis=0)  # (time, channel, sample)
    
    # Create xarray.DataArray with labeled dimensions: time, sample, RX, TX
    iq_data_xarray = xr.DataArray(
        iq_data_combined,
        dims=["sample", "TX Gain A", "TX Gain B", "RX Gain A", "RX Gain B"],
        coords={
            "sample": np.arange(iq_data_combined.shape[0]),
            "TX Gain A": np.array(tx_gain_values_a),
            "TX Gain B": np.array(tx_gain_values_b),
            "RX Gain A": np.array(rx_gain_a_values),
            "RX Gain B": np.array(rx_gain_b_values)
        },
        attrs={
            "description": "Raw IQ data stored in xarray"
        }
    )   
    # Save the xarray to a NetCDF file for efficient storage
    netcdf_filename = os.path.join(os.getcwd(), "raw_iq_data.nc")
    iq_data_xarray.to_netcdf(netcdf_filename)
    print("...Done.")
    
    print(f"Raw IQ data stored in xarray and saved as {netcdf_filename}")

# # Function to compute circular mean and circular standard deviation for RX gain B and TX gain in a CSV
# def store_circmean_and_circstd_in_xarray(iq_data, tx_gain_values_a, tx_gain_values_b, gain_b_values, rx_gain_a_values, out_dir):
#     phase_differences_by_gain = defaultdict(list)
    
#     # Loop through IQ data to calculate phase differences
#     for file_idx in range(iq_data.sizes['file']):
#         iq_data_file = iq_data.isel(file=file_idx)
        
#         # Compute phase difference for this file
#         phase_diff = compute_phase_difference(iq_data_file.values, iq_data.sizes['sample'])

#         # Extract RX gain B and TX gain from metadata
#         tx_gain_a = tx_gain_values_a[file_idx]
#         tx_gain_b = tx_gain_values_b[file_idx]
#         gain_b = gain_b_values[file_idx]
#         rx_gain_a = rx_gain_a_values[file_idx]
        
#         phase_differences_by_gain[(tx_gain_a, tx_gain_b, rx_gain_a, gain_b)] = phase_diff

#     # Create a new xarray to store the circular mean and std dev for each combination of gains
#     circ_means = np.empty((len(set(tx_gain_values_a)), len(set(tx_gain_values_b)), len(set(rx_gain_a_values)), len(set(gain_b_values))))
#     circ_vars = np.empty((len(set(tx_gain_values_a)), len(set(tx_gain_values_b)), len(set(rx_gain_a_values)), len(set(gain_b_values))))

#     for i, tx_gain_a in enumerate(sorted(set(tx_gain_values_a))):
#         for j, tx_gain_b in enumerate(sorted(set(tx_gain_values_b))):
#             for k, rx_gain_a in enumerate(sorted(set(rx_gain_a_values))):
#                 for l, gain_b in enumerate(sorted(set(gain_b_values))):
#                     key = (tx_gain_a, tx_gain_b, rx_gain_a, gain_b)
#                     phase_diff = phase_differences_by_gain.get(key, [])
#                     if phase_diff:
#                         circ_mean = circmean(phase_diff, high=np.pi, low=-np.pi)  # Circular mean in radians
#                         circ_var = circstd(phase_diff, high=np.pi, low=-np.pi) ** 2  # Circular variance
                        
#                         circ_means[i, j, k, l] = np.rad2deg(circ_mean)  # Convert to degrees
#                         circ_vars[i, j, k, l] = np.rad2deg(np.sqrt(circ_var))  # Convert variance to standard deviation (in degrees)
    
#     # Store the circular mean and std dev in an xarray
#     circmean_xarray = xr.DataArray(
#         circ_means,
#         dims=["TX Gain A", "TX Gain B", "RX Gain A", "RX Gain B"],
#         coords={
#             "TX Gain A": sorted(set(tx_gain_values_a)),
#             "TX Gain B": sorted(set(tx_gain_values_b)),
#             "RX Gain A": sorted(set(rx_gain_a_values)),
#             "RX Gain B": sorted(set(gain_b_values)),
#         },
#         attrs={
#             "description": "Circular Mean (degrees)"
#         }
#     )
    
#     circstd_xarray = xr.DataArray(
#         circ_vars,
#         dims=["TX Gain A", "TX Gain B", "RX Gain A", "RX Gain B"],
#         coords={
#             "TX Gain A": sorted(set(tx_gain_values_a)),
#             "TX Gain B": sorted(set(tx_gain_values_b)),
#             "RX Gain A": sorted(set(rx_gain_a_values)),
#             "RX Gain B": sorted(set(gain_b_values)),
#         },
#         attrs={
#             "description": "Circular Std Dev (degrees)"
#         }
#     )
    
#     # Save the circular mean and standard deviation xarray to netCDF files
#     circmean_filename = os.path.join(out_dir, "circmean.nc")
#     circstd_filename = os.path.join(out_dir, "circstd.nc")
#     circmean_xarray.to_netcdf(circmean_filename)
#     circstd_xarray.to_netcdf(circstd_filename)
    
#     print(f"Circular mean and standard deviation stored in {circmean_filename} and {circstd_filename}")

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument("--in-dir", type=str, default='./data/', help="Directory containing IQ data files and metadata (default: current directory)")
    # parser.add_argument("--out-dir", type=str, default='./results/', help="Directory output")
    args = parser.parse_args()
    
    # Store raw IQ data in xarray
    store_raw_iq_data_in_xarray()
    
    # Store phase difference and circular mean/std in xarray
    # store_circmean_and_circstd_in_xarray(iq_data, iq_data.coords['tx_gain_a'].values, iq_data.coords['tx_gain_b'].values, iq_data.coords['rx_gain_b'].values, iq_data.coords['rx_gain_a'].values, args.out_dir)

if __name__ == "__main__":
    main()
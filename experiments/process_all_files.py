import numpy as np
import os
import yaml
import argparse
import xarray as xr

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

# Step 1: Read all metadata files and organize data based on gain combinations
def read_metadata_and_organize_files(in_dir):
    # Dictionary to hold the filenames for each (TX Gain A, TX Gain B, RX Gain A, RX Gain B) tuple
    files_by_gains = {}

    # Loop through all files recursively
    for root, dirs, files in os.walk(in_dir):
        for filename in files:
            if filename.endswith(".npy"):
                # Load metadata for each IQ data file
                metadata = load_metadata_from_yml(os.path.join(root, filename))

                if metadata is None:
                    continue
                
                # Extract gain values from the metadata
                tx_gain_a = int(metadata.get('tx_gain_a', metadata.get('tx_gain', None)))  # Ensure integer
                tx_gain_b = int(metadata.get('tx_gain_b', metadata.get('tx_gain', None)))  # Ensure integer
                rx_gain_a = int(metadata['rx_gain_a'])  # Ensure integer
                rx_gain_b = int(metadata['rx_gain_b'])  # Ensure integer

                # Create the key for the gain combination
                gain_key = (tx_gain_a, tx_gain_b, rx_gain_a, rx_gain_b)

                # Store the filename for this gain combination
                if gain_key not in files_by_gains:
                    files_by_gains[gain_key] = []
                files_by_gains[gain_key].append(os.path.join(root, filename))
    
    return files_by_gains

# Step 2: Find the coordinate with the highest number of files and determine MAX_IQ_LEN
def find_max_length(files_by_gains):
    max_length = 0
    best_combination = None



    # Loop through the files by gain combination and calculate total length
    max_files = 0
    max_file_list = ()

    for _, file_list in files_by_gains.items():
        if len(file_list) > max_files:
            max_files = len(file_list)
            max_file_list = file_list

    total_length = 0
    for file in max_file_list:
        iq_data = load_iq_data(file)
        total_length += iq_data.shape[1]  # Sum the sample lengths

    return total_length

# Step 3: Create an empty xarray with the correct dimensions and coordinates
def create_empty_xarray(files_by_gains, max_length):
    # Get the unique gain values
    tx_gain_a_values = sorted(set(gain[0] for gain in files_by_gains.keys()))
    tx_gain_b_values = sorted(set(gain[1] for gain in files_by_gains.keys()))
    rx_gain_a_values = sorted(set(gain[2] for gain in files_by_gains.keys()))
    rx_gain_b_values = sorted(set(gain[3] for gain in files_by_gains.keys()))

    # Create coordinates for the xarray based on the extracted gains
    coords = {
        "TX Gain A": tx_gain_a_values,
        "TX Gain B": tx_gain_b_values,
        "RX Gain A": rx_gain_a_values,
        "RX Gain B": rx_gain_b_values,
        "sample": np.arange(max_length)  # Set sample dimension to the max length
    }

    # Initialize the xarray with empty data for the maximum length
    iq_data_xarray = xr.DataArray(
        np.empty((len(tx_gain_a_values), len(tx_gain_b_values), len(rx_gain_a_values), len(rx_gain_b_values), max_length), dtype=np.complex64),  # Placeholder shape
        dims=["TX Gain A", "TX Gain B", "RX Gain A", "RX Gain B", "sample"],
        coords=coords,
        attrs={"description": "Raw IQ data stored in xarray"}
    )

    return iq_data_xarray

# Step 4: Read the files for the best combination and populate the xarray
def populate_xarray(iq_data_xarray, files_by_gains):

    for gain_index, file_list in files_by_gains.items():
    
        tx_gain_a, tx_gain_b, rx_gain_a, rx_gain_b = gain_index

        for file in file_list:
            iq_data = load_iq_data(file)

            # Fill the xarray at the corresponding coordinate
            iq_data_xarray.loc[{"TX Gain A": tx_gain_a, "TX Gain B": tx_gain_b, "RX Gain A": rx_gain_a, "RX Gain B": rx_gain_b}] = iq_data

    return iq_data_xarray

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", type=str, default=os.getcwd(), help="Directory containing IQ data files and metadata (default: current directory)")
    args = parser.parse_args()

    # Step 1: Read metadata and organize the files by gain combination
    files_by_gains = read_metadata_and_organize_files(args.in_dir)

    # Step 2: Find the best gain combination and determine the MAX_IQ_LEN
    max_sample_length = find_max_length(files_by_gains)

    # Step 3: Create an empty xarray with the correct dimensions
    iq_data_xarray = create_empty_xarray(files_by_gains, max_sample_length)

    # Step 4: Populate the xarray with the IQ data from the files
    iq_data_xarray = populate_xarray(iq_data_xarray, files_by_gains)

    # Save xarray to a NetCDF file for efficient storage
    netcdf_filename = os.path.join(args.in_dir, "raw_iq_data.nc")
    iq_data_xarray.to_netcdf(netcdf_filename)
    
    print(f"Raw IQ data stored in xarray and saved as {netcdf_filename}")

if __name__ == "__main__":
    main()

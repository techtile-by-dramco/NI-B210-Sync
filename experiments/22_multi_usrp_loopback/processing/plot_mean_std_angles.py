import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
import re

# Function to plot the phase difference vs RX gain B with mean and variance
def plot_phase_difference_vs_gain(csv_file, save_path):
    # Load the CSV file containing circmean and circstd
    data = pd.read_csv(csv_file)

    # Extract the values
    gain_b_values = data['Meas id']
    circ_mean_deg = data['Circular Mean (degrees)']
    circ_std_deg = data['Circular Std Dev (degrees)']

    # Create the plot
    plt.figure(figsize=(8, 6))
    plt.scatter(gain_b_values, circ_mean_deg, color='b', marker='o', label='Phase Difference')
    
    # Add error bars for the variance (converted to degrees)
    plt.errorbar(gain_b_values, circ_mean_deg, yerr=circ_std_deg, fmt='o', color='b', label='Variance')

    # Format and display the plot
    plt.title('Phase Difference vs Time with Circular Variance (Mean over all files)')
    plt.xlabel('Measurement ID')
    plt.ylabel('Average Phase Difference (Degrees)')
    plt.grid(True)
    plt.legend()
    
    # Save the figure
    plot_filename = 'phase_difference_vs_time_with_variance.png'
    # plt.savefig(plot_filename) OLD WAY
    plt.savefig(os.path.join(save_path, plot_filename))
    plt.show()
    plt.close()
    
    print(f"Plot saved as {plot_filename}")

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv_file", type=str, default='./results/circmean_and_circstd.csv', 
                        help="Path to the CSV file with circmean and circstd values (default: './results/circmean_and_circstd.csv')")
    args = parser.parse_args()

    # Define the directory path where the generated figure will be saved
    save_path = os.path.dirname(os.path.dirname(args.csv_file))

    # Search for tile name
    match = re.search(r'([A-Za-z]\d{2})_', args.csv_file)
    if match:
        tile_name = match.group(0).strip('_')

    # Plot phase difference vs RX gain B with circular variance
    plot_phase_difference_vs_gain(args.csv_file, save_path)

if __name__ == "__main__":
    main()

import pandas as pd
import matplotlib.pyplot as plt
import argparse

# Function to plot the phase difference vs RX gain B with mean and variance
def plot_phase_difference_vs_gain(csv_file):
    # Load the CSV file containing circmean and circstd
    data = pd.read_csv(csv_file)

    # Create the plot
    plt.figure(figsize=(8, 6))

    # Extract the values
    data = data.groupby(["frequency"])
    for freq, grp in data:
        gain_b_values = grp['RX Gain B'].to_numpy()
        circ_mean_deg = grp['Circular Mean (degrees)'].to_numpy()
        circ_std_deg = grp['Circular Std Dev (degrees)'].to_numpy()

        # idx = gain_b_values.tolist().index(30)

        # plt.scatter(gain_b_values, circ_mean_deg-circ_mean_deg[idx], marker='o', label=freq)
        # plt.errorbar(gain_b_values, circ_mean_deg-circ_mean_deg[idx], yerr=circ_std_deg, fmt='o')

        plt.scatter(gain_b_values, circ_mean_deg, marker='o', label=f"{freq[0]/1e6:.0f} MHz")
        plt.errorbar(gain_b_values, circ_mean_deg, yerr=circ_std_deg, fmt='o')

    # Format and display the plot
    plt.title('Phase Difference vs RX Gain B with Circular Variance (Mean over all files)')
    plt.xlabel('RX Gain B')
    plt.ylabel('Average Phase Difference (Degrees)')
    plt.grid(True)
    plt.legend()
    
    # Save the figure
    plot_filename = 'phase_difference_vs_gainB_with_variance.png'
    plt.savefig(plot_filename)
    plt.show()
    plt.close()
    
    print(f"Plot saved as {plot_filename}")

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv_file", type=str, default='./results/circmean_and_circstd.csv', 
                        help="Path to the CSV file with circmean and circstd values (default: './results/circmean_and_circstd.csv')")
    args = parser.parse_args()

    # Plot phase difference vs RX gain B with circular variance
    plot_phase_difference_vs_gain(args.csv_file)

if __name__ == "__main__":
    main()

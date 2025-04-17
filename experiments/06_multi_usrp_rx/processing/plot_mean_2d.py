import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse

# Function to read the CSV file and plot the circular mean as a heatmap
def plot_circular_mean_heatmap(csv_file):
    # Load the CSV file containing circmean and circstd
    data = pd.read_csv(csv_file)

    data = data.groupby("hostname")

    for hostname, df in data:

        # Extract the unique RX Gain A and RX Gain B values
        gain_a = sorted(df['RX Gain A'].unique())  # Sort RX Gain A values
        gain_b = sorted(df['RX Gain B'].unique())  # Sort RX Gain B values
        

        # Initialize a matrix for circular means
        circ_mean_matrix = np.full((len(gain_a), len(gain_b)), np.nan)
        circ_std_matrix = np.full((len(gain_a), len(gain_b)), np.nan)

        # Fill the matrix with circular mean values
        for _, row in df.iterrows():
            gain_a_idx = gain_a.index(row['RX Gain A'])
            gain_b_idx = gain_b.index(row['RX Gain B'])
            circ_mean_matrix[gain_a_idx, gain_b_idx] = row['Circular Mean (degrees)']
            circ_std_matrix[gain_a_idx, gain_b_idx] = row['Circular Std Dev (degrees)']

        # Create the heatmap plot using imshow
        plt.figure(figsize=(8, 6))
        plt.imshow(circ_mean_matrix, aspect='auto', cmap='viridis', origin='lower', interpolation='nearest')

        # Add color bar
        cbar = plt.colorbar()
        cbar.set_label('Circular Mean (degrees)')

        # Set the axis labels
        plt.xticks(np.arange(len(gain_b)), gain_b, rotation=90)
        plt.yticks(np.arange(len(gain_a)), gain_a)

        plt.xlabel('RX Gain B')
        plt.ylabel('RX Gain A')

        # Set title
        plt.title('Circular Mean vs RX Gain A and RX Gain B')

        # Save the figure
        plot_filename = f'{hostname}_circular_mean_heatmap.png'
        plt.tight_layout()  # Adjust layout to prevent overlapping
        plt.savefig(plot_filename)
        plt.show()

        print(f"Heatmap plot saved as {plot_filename}")


        # Create the heatmap plot using imshow
        plt.figure(figsize=(8, 6))
        plt.imshow(circ_std_matrix, aspect='auto', cmap='viridis', origin='lower', interpolation='nearest')

        # Add color bar
        cbar = plt.colorbar()
        cbar.set_label('Circular Std Dev (degrees)')

        # Set the axis labels
        plt.xticks(np.arange(len(gain_b)), gain_b, rotation=90)
        plt.yticks(np.arange(len(gain_a)), gain_a)

        plt.xlabel('RX Gain B')
        plt.ylabel('RX Gain A')

        # Set title
        plt.title('Circular Mean vs RX Gain A and RX Gain B')

        # Save the figure
        plot_filename = f'{hostname}_circular_std_heatmap.png'
        plt.tight_layout()  # Adjust layout to prevent overlapping
        plt.savefig(plot_filename)
        plt.show()

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv_file", type=str, default='./results/circmean_and_circstd.csv',
                        help="Path to the CSV file with circmean and circstd values (default: './results/circmean_and_circstd_rx_gain_a_b.csv')")
    args = parser.parse_args()

    # Plot circular mean heatmap
    plot_circular_mean_heatmap(args.csv_file)

if __name__ == "__main__":
    main()

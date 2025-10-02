import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # nodig voor 3D plot
import numpy as np
import argparse

# Function to read the CSV file and plot the circular mean as a heatmap
def plot_circular_mean_heatmap(csv_file):
    # Load the CSV file containing circmean and circstd
    data = pd.read_csv(csv_file)

    # --- 3D Plot ---
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")

    ax.scatter(
        data["RX Gain A"],
        data["RX Gain B"],
        data["Circular Mean (degrees)"],
        c=data["Circular Mean (degrees)"],  # kleur op basis van Circular Mean
        cmap="viridis",
        s=40
    )

    ax.set_xlabel("RX Gain A")
    ax.set_ylabel("RX Gain B")
    ax.set_zlabel("Circular Mean (degrees)")
    ax.set_title("3D plot van RX Gain A, RX Gain B en Circular Mean")

    plt.colorbar(ax.scatter(
        data["RX Gain A"], data["RX Gain B"], data["Circular Mean (degrees)"],
        c=data["Circular Mean (degrees)"], cmap="viridis", s=40
    ), ax=ax, shrink=0.5, aspect=10, label="Circular Mean")

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

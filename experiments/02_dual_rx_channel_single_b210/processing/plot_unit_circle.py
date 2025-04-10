import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import argparse

# Function to create a circular plot with color bands based on RX Gain B
def plot_circular_with_gain(csv_file):
    # Load the CSV file containing circmean and circstd
    data = pd.read_csv(csv_file)

    # Extract the values
    gains = data['RX Gain B']
    phases = data['Circular Mean (degrees)']

    # Create the polar plot
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, polar=True)

    # Threshold
    threshold = 33
    low_mask = gains <= threshold
    high_mask = gains > threshold

    gains_low = gains[low_mask]
    phases_low = phases[low_mask]

    gains_high = gains[high_mask]
    phases_high = phases[high_mask]

    # Colormaps
    cmap_low = plt.cm.spring
    cmap_high = plt.cm.winter

    # Normalizers (independent for hard split)
    norm_low = Normalize(vmin=gains_low.min(), vmax=gains_low.max())
    norm_high = Normalize(vmin=gains_high.min(), vmax=gains_high.max())

    ax.set_ylim(0, 1)  # Set radius limit


    # Wedge width in degrees
    angle_width_deg = 1.0
    ring_radius = 1.0
    ring_width = 0.2

    def draw_wedge(theta_deg, color):
        start_angle = theta_deg - angle_width_deg / 2
        end_angle = theta_deg + angle_width_deg / 2
        wedge = Wedge(center=(0, 0), r=ring_radius, width=ring_width,
                    theta1=start_angle, theta2=end_angle,
                    facecolor=color, linewidth=0.2,
                    transform=ax.transData._b, alpha=0.5)
        ax.add_patch(wedge)

    # Draw low gain wedges (Blues)
    for gain, phase in zip(gains_low, phases_low):
        color = cmap_low(norm_low(gain))
        draw_wedge(phase, color)

    # Draw high gain wedges (Reds)
    for gain, phase in zip(gains_high, phases_high):
        color = cmap_high(norm_high(gain))
        draw_wedge(phase, color)

    # Colorbar 1: gain ≤ 33
    sm_low = ScalarMappable(cmap=cmap_low, norm=norm_low)
    sm_low.set_array([])
    cbar_low = plt.colorbar(sm_low, ax=ax, pad=0.05, orientation='vertical', fraction=0.03)
    cbar_low.set_label("Gain ≤ 33")

    # Colorbar 2: gain > 33
    sm_high = ScalarMappable(cmap=cmap_high, norm=norm_high)
    sm_high.set_array([])
    cbar_high = plt.colorbar(sm_high, ax=ax, pad=0.15, orientation='vertical', fraction=0.03)
    cbar_high.set_label("Gain > 33")

    plt.title("Phase by Gain with Hard-Colormap Split at 33", va='bottom')
    plt.tight_layout()
    ax.set_rticks([])  # Hide radial ticks
    ax.set_yticklabels([])  # Hide radial labels

    # Save the polar plot
    polar_plot_filename = 'phase_difference_polar_plot.png'
    plt.savefig(polar_plot_filename)
    plt.show()
    plt.close()

    print(f"Polar plot saved as {polar_plot_filename}")

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv_file", type=str, default='./results/circmean_and_circstd.csv', 
                        help="Path to the CSV file with circmean and circstd values (default: './results/circmean_and_circstd.csv')")
    args = parser.parse_args()

    # Create a circular plot based on RX Gain B color bands
    plot_circular_with_gain(args.csv_file)

if __name__ == "__main__":
    main()

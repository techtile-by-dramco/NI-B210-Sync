import pandas as pd
import matplotlib.pyplot as plt
import argparse

# Function to read the CSV and plot phase differences with error bars
def plot_phase_with_error_bars(csv_file, output_dir):
    # Read the CSV data
    data = pd.read_csv(csv_file)
    
    # Group the data by hostname
    grouped_data = data.groupby('hostname')

    plt.figure(figsize=(10, 6))
    # Loop through each group (hostname) and plot the phase mean and standard deviation as error bars
    for hostname, hostname_data in grouped_data:
        # Plot the circular mean (phase) with error bars (std dev)
       
        plt.errorbar(pd.to_datetime(hostname_data['Timestamp']), 
                     hostname_data['Circular Mean (degrees)'], 
                     yerr=hostname_data['Circular Std Dev (degrees)'], 
                     fmt='o', label=hostname, capsize=3, elinewidth=2)
        
    # Format the plot
    plt.title(f"Phase Difference over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Phase (degrees)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # Save the plot to the output directory
    plot_filename = f"phase_with_error_bars.png"
    plt.savefig(f"{output_dir}/{plot_filename}")
    plt.close()
    
    print(f"Plot for {hostname} saved as {output_dir}/{plot_filename}")

# Main function to run the script
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-file", type=str, default='./results/circmean_and_circstd_by_timestamp.csv', help="CSV file with phase difference data")
    parser.add_argument("--output-dir", type=str, default='./results/', help="Directory to save the plots")
    args = parser.parse_args()

    # Plot the phase difference with error bars for each hostname
    plot_phase_with_error_bars(args.csv_file, args.output_dir)

if __name__ == "__main__":
    main()

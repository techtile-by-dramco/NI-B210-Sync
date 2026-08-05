## 06_multi_usrp_rx

One testtile that transmit a sine wave
```
python3 examples/tx_waveforms.py  --args "type=b200" --freq 920e6 --rate 1e6 --duration 1e8 --channels 0 --wave-freq 0e5 --wave-ampl 0.8 --gain 70
```

### Connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| ALL["T04 source and T05–T08 receivers"]
    T04["T04 CH0 TX/RX<br/>920 MHz CW"] --> ATT["Rated attenuation"] --> SPLIT["ZC16PD-252-S+ splitter<br/>8 outputs used"]
    SPLIT -->|"outputs 1–2"| T05["T05 CH0 RX2<br/>and CH1 RX2"]
    SPLIT -->|"outputs 3–4"| T06["T06 CH0 RX2<br/>and CH1 RX2"]
    SPLIT -->|"outputs 5–6"| T07["T07 CH0 RX2<br/>and CH1 RX2"]
    SPLIT -->|"outputs 7–8"| T08["T08 CH0 RX2<br/>and CH1 RX2"]
```

Measure the T04 power after attenuation and splitter loss before connecting any receiver. Keep each splitter output and cable assigned to the same RX port for the complete sweep.

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/pictures/setup_6_front.jpg" width="200"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/pictures/setup_6_rear.jpg" width="200"></td>
    <td>
  
| ⚙️ Bash Settings   | Value | Unit |
|--------------|----------|-|
| GAIN_A       | 30       | dB |
| GAIN_B_START | 7        | dB |
| GAIN_B_STOP  | 48       | dB |
| GAIN_STEP    | 1        | dB |
| ITERATIONS [G]   | 2    | - |

</td><td>
  
| ⚙️ Python Settings | Value | Unit |
|--------------|----------|-|
| CLOCK_TIMEOUT  | 1000   | ms |
| INIT_DELAY     | 0.2    | s |
| RATE           | 250e3  | Hz |
| FREQ           | 920e6  | Hz |
| CAPTURE_TIME   | 2      | s |
| / | | |

</td></tr></table>

### Processing data

- **Create csv files** Mount the whole RPI folder structure via Samba to your PC to do the processing locally.
  Mount RPI folder en parse the location of the raw data, e.g.:
  - `W:\NI-B210-Sync\experiments\06_multi_usrp_rx\client\rawdata`
  - `X:\NI-B210-Sync\experiments\06_multi_usrp_rx\client\rawdata`
  - `V:\NI-B210-Sync\experiments\06_multi_usrp_rx\client\rawdata`
  - `U:\NI-B210-Sync\experiments\06_multi_usrp_rx\client\rawdata`

```
python experiments\06_multi_usrp_rx\processing\store_phase_difference.py --in-dir W:\NI-B210-Sync\experiments\06_multi_usrp_rx\client\rawdata --out-dir experiments\06_multi_usrp_rx\results
python experiments\06_multi_usrp_rx\processing\store_phase_difference.py --in-dir x:\NI-B210-Sync\experiments\06_multi_usrp_rx\client\rawdata --out-dir experiments\06_multi_usrp_rx\results
python experiments\06_multi_usrp_rx\processing\store_phase_difference.py --in-dir V:\NI-B210-Sync\experiments\06_multi_usrp_rx\client\rawdata --out-dir experiments\06_multi_usrp_rx\results
python experiments\06_multi_usrp_rx\processing\store_phase_difference.py --in-dir U:\NI-B210-Sync\experiments\06_multi_usrp_rx\client\rawdata --out-dir experiments\06_multi_usrp_rx\results
```

- **Create plots** plot_unit_circle
```
python .\experiments\06_multi_usrp_rx\processing\plot_unit_circle.py --csv_file .\experiments\06_multi_usrp_rx\results\T05_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx\processing\plot_unit_circle.py --csv_file .\experiments\06_multi_usrp_rx\results\T06_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx\processing\plot_unit_circle.py --csv_file .\experiments\06_multi_usrp_rx\results\T07_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx\processing\plot_unit_circle.py --csv_file .\experiments\06_multi_usrp_rx\results\T08_circmean_and_circstd.csv 
```

- **Create plots** plot_mean_2d
```
python .\experiments\06_multi_usrp_rx\processing\plot_mean_2d.py --csv_file .\experiments\06_multi_usrp_rx\results\T05_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx\processing\plot_mean_2d.py --csv_file .\experiments\06_multi_usrp_rx\results\T06_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx\processing\plot_mean_2d.py --csv_file .\experiments\06_multi_usrp_rx\results\T07_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx\processing\plot_mean_2d.py --csv_file .\experiments\06_multi_usrp_rx\results\T08_circmean_and_circstd.csv 
```

- **Create plots** plot_mean_std_angles
```
python .\experiments\06_multi_usrp_rx\processing\plot_mean_std_angles.py --csv_file .\experiments\06_multi_usrp_rx\results\circmean_and_circstd.csv
```

### Results [J] (plot_unit_circle)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T05_phase_difference_polar_plot.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T06_phase_difference_polar_plot.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T07_phase_difference_polar_plot.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T08_phase_difference_polar_plot.png" width="400"></td>
  </tr>
</table>

### Results [J] (plot_mean_2d)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T05_circular_mean_heatmap.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T06_circular_mean_heatmap.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T07_circular_mean_heatmap.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T08_circular_mean_heatmap.png" width="400"></td>
  </tr>
</table>

### Results [J] (plot_std_2d)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T05_circular_std_heatmap.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T06_circular_std_heatmap.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T07_circular_std_heatmap.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/T08_circular_std_heatmap.png" width="400"></td>
  </tr>
</table>

### Results [J] (phase_difference_vs_gainB_with_variance) [TX gain T04 was 70]

<img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx/phase_difference_vs_gainB_with_variance.png" width="800">

### Results [G] (phase_difference_vs_gainB_with_variance)

<img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_old/phase_difference_vs_gainB_with_variance.png" width="800">

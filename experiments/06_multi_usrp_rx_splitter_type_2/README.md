<!-- **************************************************************************************************************************** -->
## 06_multi_usrp_rx_splitter_type_2_splitter_type_2

Same expirement als 06_multi_usrp_rx but with another RF splitter.
RF splitter [ZC16PD-252-S+](https://www.minicircuits.com/pdfs/ZC16PD-252-S+.pdf) used in "06_multi_usrp_rx" has PHASE UNBALANCE up to 18 degrees and it depends on the frequency band.

One testtile that transmit a sine wave
```
python3 examples/tx_waveforms.py  --args "type=b200" --freq 920e6 --rate 1e6 --duration 1e8 --channels 0 --wave-freq 0e5 --wave-ampl 0.8 --gain 70
```

### Connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| ALL["T04 source and T05–T08 receivers"]
    T04["T04 CH0 TX/RX<br/>920 MHz CW"] --> ATT["Rated attenuation"] --> SPLIT["Type-2 low-phase-imbalance<br/>RF distribution"]
    SPLIT -->|"two outputs"| T05["T05 CH0 RX2<br/>and CH1 RX2"]
    SPLIT -->|"two outputs"| T06["T06 CH0 RX2<br/>and CH1 RX2"]
    SPLIT -->|"two outputs"| T07["T07 CH0 RX2<br/>and CH1 RX2"]
    SPLIT -->|"two outputs"| T08["T08 CH0 RX2<br/>and CH1 RX2"]
```

Record the type-2 splitter output-to-port mapping rather than substituting the ZC16PD mapping from the preceding experiment. Measure safe input power at the highest T04 gain before connecting T05–T08.

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/pictures/front.jpg" width="400"></td>
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
  - `W:\NI-B210-Sync\experiments\06_multi_usrp_rx_splitter_type_2\client\rawdata`
  - `X:\NI-B210-Sync\experiments\06_multi_usrp_rx_splitter_type_2\client\rawdata`
  - `V:\NI-B210-Sync\experiments\06_multi_usrp_rx_splitter_type_2\client\rawdata`
  - `U:\NI-B210-Sync\experiments\06_multi_usrp_rx_splitter_type_2\client\rawdata`

```
python experiments\06_multi_usrp_rx_splitter_type_2\processing\store_phase_difference.py --in-dir W:\NI-B210-Sync\experiments\06_multi_usrp_rx_splitter_type_2\client\rawdata --out-dir experiments\06_multi_usrp_rx_splitter_type_2\results
python experiments\06_multi_usrp_rx_splitter_type_2\processing\store_phase_difference.py --in-dir x:\NI-B210-Sync\experiments\06_multi_usrp_rx_splitter_type_2\client\rawdata --out-dir experiments\06_multi_usrp_rx_splitter_type_2\results
python experiments\06_multi_usrp_rx_splitter_type_2\processing\store_phase_difference.py --in-dir V:\NI-B210-Sync\experiments\06_multi_usrp_rx_splitter_type_2\client\rawdata --out-dir experiments\06_multi_usrp_rx_splitter_type_2\results
python experiments\06_multi_usrp_rx_splitter_type_2\processing\store_phase_difference.py --in-dir U:\NI-B210-Sync\experiments\06_multi_usrp_rx_splitter_type_2\client\rawdata --out-dir experiments\06_multi_usrp_rx_splitter_type_2\results
```

- **Create plots** plot_unit_circle
```
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_unit_circle.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T05_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_unit_circle.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T06_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_unit_circle.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T07_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_unit_circle.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T08_circmean_and_circstd.csv 
```

- **Create plots** plot_mean_2d
```
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_mean_2d.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T05_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_mean_2d.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T06_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_mean_2d.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T07_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_mean_2d.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T08_circmean_and_circstd.csv 
```

- **Create plots** plot_mean_std_angles_per_usrp
```
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_mean_std_angles_per_usrp.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T05_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_mean_std_angles_per_usrp.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T06_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_mean_std_angles_per_usrp.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T07_circmean_and_circstd.csv 
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_mean_std_angles_per_usrp.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\T08_circmean_and_circstd.csv 
```

- **Create plots** plot_mean_std_angles
```
python .\experiments\06_multi_usrp_rx_splitter_type_2\processing\plot_mean_std_angles.py --csv_file .\experiments\06_multi_usrp_rx_splitter_type_2\results\circmean_and_circstd.csv
```

### Results [J] (plot_unit_circle)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T05_phase_difference_polar_plot.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T06_phase_difference_polar_plot.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T07_phase_difference_polar_plot.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T08_phase_difference_polar_plot.png" width="400"></td>
  </tr>
</table>

### Results [J] (plot_mean_2d)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T05_circular_mean_heatmap.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T06_circular_mean_heatmap.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T07_circular_mean_heatmap.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T08_circular_mean_heatmap.png" width="400"></td>
  </tr>
</table>

### Results [J] (plot_std_2d)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T05_circular_std_heatmap.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T06_circular_std_heatmap.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T07_circular_std_heatmap.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T08_circular_std_heatmap.png" width="400"></td>
  </tr>
</table>

### Results [J] (phase_difference_vs_gainB_with_variance per usrp) + (plot_max_iq_per_usrp)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T05_phase_difference_vs_gainB_with_variance.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T05_max_iq_vs_gainB.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T06_phase_difference_vs_gainB_with_variance.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T06_max_iq_vs_gainB.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T07_phase_difference_vs_gainB_with_variance.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T07_max_iq_vs_gainB.png" width="400"></td>
  </tr>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T08_phase_difference_vs_gainB_with_variance.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/T08_max_iq_vs_gainB.png" width="400"></td>
  </tr>
</table>

### Results [J] (phase_difference_vs_gainB_with_variance) [TX gain T04 was 70]

<img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/06_multi_usrp_rx_splitter_type_2/phase_difference_vs_gainB_with_variance.png" width="800">

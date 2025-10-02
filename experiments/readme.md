This folder contains scripts and results to investigate the phase stability and coherency of the B210 for multi-device phase-coherent operation.


<!-- **************************************************************************************************************************** -->
### 1️⃣ Setup
  - 🔩 **Hardware** 🔩: a single USRP B210 (it has 2 transmitters and 2 receivers that are phase-coherent because they share the same local oscillator).
  - 🔌**Connection**🔌: the TX output is looped back to the RX inputs using an SMA cable and a 20 dB attenuator, so the signal can be tested without antennas and without overloading the receiver.

### 2️⃣ Goal of the experiment 
The goal is to **investigate** how the TX or RX **gain** configuration affects the **phase difference** between the two RX channels.
  - Normally, the channels are coherent, meaning their phase relationship should remain fixed.
  - By varying the RX gain, one can check if this introduces additional phase shifts.
<!-- **************************************************************************************************************************** -->

<!-- **************************************************************************************************************************** -->
## 01_dual_rx_channel_single_b210

In this experiment, a single B210 is used. The RX and TX channels are connected with an SMA cable and a 20 dB attenutator.
The goal is to determine the effect of RX gain configuration on the phase difference between the two channels.
Given that using one B210 ensures phase-coherency between the channels, we can see when a phase differences changes based on the gain index.

In the first setup, the setup ensured as equal path lengths as possible by using the same cables and attenutator.

### Setup

🆔 Identifiers 🆔 [EXP_ID == exp_test] & [MEAS_ID == 1]

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/01_dual_rx_channel_single_b210/setup-1.jpg" width="200"></td>
    <td>
  
| ⚙️ Bash Settings   | Value | Unit |
|--------------|----------|-|
| TX_GAIN      | 38       | dB |
| GAIN_A       | 30       | dB |
| GAIN_B_START | 7        | dB |
| GAIN_B_STOP  | 55       | dB |
| GAIN_STEP    | 1        | dB |
| ITERATIONS   | 100      | - |

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

### Results
When adjusting the gain of channel B, a phase shift occurs at the transition from 33 dB to 34 dB. Below 33 dB, the phase difference is 0 degrees, whereas above 34 dB, the phase difference is 180 degrees.
<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/01_dual_rx_channel_single_b210/phase_difference_vs_gainB_with_variance.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/01_dual_rx_channel_single_b210/phase_difference_polar_plot.png" width="400"></td>
  </tr>
</table>


<!-- **************************************************************************************************************************** -->
## 02_dual_rx_channel_single_b210

In the 2nd setup a longer cable is connected to A/B. This induces an additional phase difference between the two channels. This was done intentionally as small IQ values could result in phase differences close to zero. 
Same as 01 but with setup 2 (ie one cable is longer than the other to induce an additional phase shift between the two RX-TX chains)

### Setup
🆔 Identifiers 🆔 [EXP_ID == exp_test] & [MEAS_ID == 1]

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/02_dual_rx_channel_single_b210/setup-2.jpg" width="200"></td>
    <td>
  
| ⚙️ Bash Settings   | Value | Unit |
|--------------|----------|-|
| TX_GAIN      | 38       | dB |
| GAIN_A       | 30       | dB |
| GAIN_B_START | 7        | dB |
| GAIN_B_STOP  | 55       | dB |
| GAIN_STEP    | 1        | dB |
| ITERATIONS   | 100      | - |

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

- **Create csv file** Mount the whole RPI folder structure via Samba to your PC to do the processing locally.
  Mount RPI folder en parse the location of the raw data `W:\NI-B210-Sync\experiments\02_dual_rx_channel_single_b210\client\rawdata`

```
python experiments\02_dual_rx_channel_single_b210\processing\store_phase_difference.py --in-dir W:\NI-B210-Sync\experiments\02_dual_rx_channel_single_b210\client\rawdata --out-dir experiments\02_dual_rx_channel_single_b210\\results
```

- **Create plots** plot_unit_circle
```
python .\experiments\02_dual_rx_channel_single_b210\processing\plot_unit_circle.py --csv_file .\experiments\02_dual_rx_channel_single_b210\results\circmean_and_circstd.csv 
```

- **Create plots** plot_unit_circle
```
python .\experiments\02_dual_rx_channel_single_b210\processing\plot_mean_std_angles.py --csv_file .\experiments\02_dual_rx_channel_single_b210\results\circmean_and_circstd.csv
```

### Results

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/02_dual_rx_channel_single_b210/phase_difference_vs_gainB_with_variance.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/02_dual_rx_channel_single_b210/phase_difference_polar_plot.png" width="400"></td>
  </tr>
</table>

<!-- **************************************************************************************************************************** -->
## 03_dual_tx_channel_single_b210

Same as 02 but now the RX gains are fixed and the TX gains are varied.

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/02_dual_rx_channel_single_b210/setup-2.jpg" width="200"></td>
    <td>
  
| ⚙️ Bash Settings   | Value | Unit |
|--------------|----------|-|
| TX_GAIN      | 30       | dB |
| GAIN_A       | 50       | dB |
| GAIN_B_START | 1        | dB |
| GAIN_B_STOP  | 63       | dB |
| GAIN_STEP    | 1        | dB |
| ITERATIONS [J]   | 1    | - |
| ITERATIONS [G]   | 100  | - |

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

- **Create csv file** Mount the whole RPI folder structure via Samba to your PC to do the processing locally.
  Mount RPI folder en parse the location of the raw data `W:\NI-B210-Sync\experiments\02_dual_rx_channel_single_b210\client\rawdata`

```
python experiments\03_dual_tx_channel_single_b210\processing\store_phase_difference.py --in-dir W:\NI-B210-Sync\experiments\03_dual_tx_channel_single_b210\client\rawdata --out-dir experiments\03_dual_tx_channel_single_b210\results
```

- **Create plots** plot_unit_circle
```
python .\experiments\03_dual_tx_channel_single_b210\processing\plot_unit_circle.py --csv_file .\experiments\03_dual_tx_channel_single_b210\results\circmean_and_circstd.csv 
```

- **Create plots** plot_unit_circle
```
python .\experiments\03_dual_tx_channel_single_b210\processing\plot_mean_std_angles.py --csv_file .\experiments\03_dual_tx_channel_single_b210\results\circmean_and_circstd.csv
```

### Results [J] (one iterations)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/03_dual_tx_channel_single_b210/phase_difference_vs_gainB_with_variance.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/03_dual_tx_channel_single_b210/phase_difference_polar_plot.png" width="400"></td>
  </tr>
</table>

### Results [G] (multiple iterations)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/03_dual_tx_channel_single_b210/archive/phase_difference_vs_gainB_with_variance.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/03_dual_tx_channel_single_b210/archive/phase_difference_polar_plot.png" width="400"></td>
  </tr>
</table>

<!-- **************************************************************************************************************************** -->
## 04_dual_rx_matrix_single_b210

Same as 02 but now both the RX A and RX B are varied, yielding a matrix of phase differences. Keeping TX constant.

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/02_dual_rx_channel_single_b210/setup-2.jpg" width="200"></td>
    <td>
  
| ⚙️ Bash Settings   | Value | Unit |
|--------------|----------|-|
| TX_GAIN      | 38       | dB |
| GAIN_A_START | 7        | dB |
| GAIN_A_STOP  | 55       | dB |
| GAIN_B_START | 7        | dB |
| GAIN_B_STOP  | 55       | dB |
| GAIN_STEP    | 1        | dB |
| ITERATIONS [J]   | 1    | - |
| ITERATIONS [G]   | 100  | - |

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

- **Create plots** plot_mean_2d
```
python .\experiments\04_dual_rx_matrix_single_b210\processing\plot_mean_2d.py --csv_file .\experiments\04_dual_rx_matrix_single_b210\results\circmean_and_circstd_1.csv 
```

- **Create plots** plot_mean_3d
```
python .\experiments\04_dual_rx_matrix_single_b210\processing\plot_mean_3d.py --csv_file .\experiments\04_dual_rx_matrix_single_b210\results\circmean_and_circstd_1.csv
```

### Results [G] (multiple iterations)

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/04_dual_rx_matrix_single_b210/circular_mean_heatmap.png" width="400"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/04_dual_rx_matrix_single_b210/circular_std_heatmap.png" width="400"></td>
  </tr>
    <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/04_dual_rx_matrix_single_b210/circular_mean_heatmap_3d.png" width="400"></td>
    <td></td>
  </tr>
</table>

These figures clearly show that an **additional phase difference** 
- can arise between RX A and RX B when both receivers operate at different gain levels. ⚠️⚠️⚠️
- as long as the gain is the same for both, there is almost no phase difference. ✅✅✅

❓Questions❓
- Do we consistently obtain the same phase differences between channel A and channel B as a function of RX Gain A and RX Gain B.
- If yes, we can make a lookup table/model?

<!-- **************************************************************************************************************************** -->
## 05

Scripts to extract relevant rates and configuration from trace logging.

<!-- **************************************************************************************************************************** -->
## 06 

Fixed RX gains

4 USRPs are connected to one splitter with equal length cables. Phase differences are checked on the scope and they were aligned <1°. 


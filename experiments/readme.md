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
## 05_vco_rates

Scripts to extract relevant rates and configuration from trace logging.

🔎 Baseband clock PLL settings: Script performs a sweep over different master clock rates. This clarifies how the B210 configures following parameters:
- **rate** → requested clock rate
- **vcorate** → oscillator frequency
- **vcodiv** → divider value
- **nint / nfrac** → integer and fractional N divider values
- **adcclk** → effective ADC-clock
- **divfactor** → internal devider factor

|master_clock_rate |       rate |divfactor  |    vcorate  |vcodiv  |nint  | nfrac  |    adcclk |
|-|-|-|-|-|-|-|-|
|         4000000.0|  64000000.0|      16.0 |1024000000.0 |     16 |   25 |1253376 | 64000000.0|
|         8000000.0| 128000000.0|      16.0 |1024000000.0 |      8 |   25 |1253376 |128000000.0|
|        10000000.0| 160000000.0|      16.0 |1280000000.0 |      8 |   32 |      0 |160000000.0|
|        12500000.0| 200000000.0|      16.0 | 800000000.0 |      4 |   20 |      0 |200000000.0|
|        16000000.0| 256000000.0|      16.0 |1024000000.0 |      4 |   25 |1253376 |256000000.0|
|        20000000.0| 320000000.0|      16.0 |1280000000.0 |      4 |   32 |      0 |320000000.0|
|        25000000.0| 400000000.0|      16.0 | 800000000.0 |      2 |   20 |      0 |400000000.0|
|        32000000.0| 512000000.0|      16.0 |1024000000.0 |      2 |   25 |1253376 |512000000.0|
|        40000000.0| 640000000.0|      16.0 |1280000000.0 |      2 |   32 |      0 |640000000.0|
|        50000000.0| 600000000.0|      12.0 |1200000000.0 |      2 |   30 |      0 |600000000.0|
|        61000000.0| 488000000.0|       8.0 | 976000000.0 |      2 |   24 | 835584 |488000000.0|

<!-- **************************************************************************************************************************** -->
## 06_multi_usrp_rx

One testtile that transmit a sine wave
```
python3 examples/tx_waveforms.py  --args "type=b200" --freq 920e6 --rate 1e6 --duration 1e8 --channels 0 --wave-freq 0e5 --wave-ampl 0.8 --gain 70
```

Measurements above --> only one USRP used --> Two times loop back --> and results of RX channels were compared.

Fixd TX signal

4 USRPs are connected to one splitter with equal length cables. Phase differences are checked on the scope and they were aligned <1°. 

One constant reference signal generated by another USRP (PPS + 10 MHz connected)
Reference signal --> connected to 4 USRPs that runs same script as experiment 02/03??? 
--> RX gain is swept

splitter output connected with 8 cables to all RX channels of the four USRPs

Gain channel 1 constant en sweep in channel B gain

Asjustments iq_capture_b210.py compare to exp e.g. 02
- TX_A and TX_B removed
- TX_CHANNELS removed
- tune_usrp is simplified --> only rx instructions!!
- tx_ref function is removed !!

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

<!-- **************************************************************************************************************************** -->
## 06_multi_usrp_rx_splitter_type_2

Same expirement als 06_multi_usrp_rx but with another RF splitter.
RF splitter [ZC16PD-252-S+](https://www.minicircuits.com/pdfs/ZC16PD-252-S+.pdf) used in "06_multi_usrp_rx" has PHASE UNBALANCE up to 18 degrees and it depends on the frequency band.

Therefore we used/made a more accurates splitter design.

More information about this experiement [here](https://github.com/techtile-by-dramco/NI-B210-Sync/tree/main/experiments/06_multi_usrp_rx_splitter_type_2).

<!-- **************************************************************************************************************************** -->
## 07 multi_usrp_rx_time

One testtile that transmit a sine wave
```
python3 examples/tx_waveforms.py  --args "type=b200" --freq 920e6 --rate 1e6 --duration 1e8 --channels 0 --wave-freq 0e5 --wave-ampl 0.8 --gain 70
```
Transmit tiles connected to 8 way splitter. Eight outputs are connected to every input channel of every USRP (same as 06).

Four USRPs measures every houre the phase difference between his two channels.

Measure 100 houres

### Results [G]
<img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/07_multi_usrp_rx_time_old/results/phase_with_error_bars.png" width="800">

<!-- **************************************************************************************************************************** -->
## 08 multi_usrp_ideal_snr

In part 06 (last figure), we observe a low SNR at an RX gain of (for example) 35 (across all USRPs) and a TX gain of 70 at T04. We're wondering why this happens:
- Is it because there's an ideal SNR between the transmitter and receiver?
- Or is this something fixed, independent of the strength of the TX signal?

<!-- **************************************************************************************************************************** -->
## 09 

<!-- **************************************************************************************************************************** -->
## 10 

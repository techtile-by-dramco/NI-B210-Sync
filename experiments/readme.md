# Experiment index

This folder contains scripts and results investigating B210 phase stability and multi-device coherent operation. Historical experiments retain their original numbering and results; new work uses one directory per reproducible experiment.

## T05–T08 testbench — current work

| Experiment | Manuscript question | Status |
|---|---|---|
| [50 — state characterization](50_t05_t08_state_characterization/README.md) | Which initialization and configuration events change the B210 phase state? | Ready to conduct |
| [51 — coherent combining](51_t05_t08_coherent_combining/README.md) | Does calibrated received power approach coherent \(M^2\) scaling for 1–4 transmitters? | Ready to conduct |
| [52 — stability and events](52_t05_t08_stability_events/README.md) | How fast does phase drift, and which events require recalibration? | Ready to conduct |
| [60 — ZMQ GPIO-arrival timing](60_t05_t08_zmq_gpio_arrival/README.md) | What is the scope-measured spread of T05–T08 GPIO rises after one common ZMQ message? | Ready to conduct |

T04 is the common RF source for experiments 50–52; T05–T08 are the devices under test. Experiment 60 instead measures host/network notification timing with GPIO outputs and one shared scope timebase, so it has no RF wiring. Shared, tested acquisition, source, and analysis code for the RF work lives in `t05_t08_common/`. Runtime output goes into an ignored `runs/` directory. Hardware runs reject and separately log missing reference lock, late first-sample timestamps, RX overflow/timeout, and TX asynchronous errors.

The full-ceiling experiment from the manuscript is intentionally deferred: this first pass is limited to the controlled T05–T08 bench.

## Historical experiment connection guides

Each historical directory now has a local connection guide derived from its code, photographs, configuration, and the original notes below. Guides marked archived, inferred, or prototype identify missing information that must be checked before reconnecting hardware.

- [01 — single-B210 RX-gain sweep](01_dual_rx_channel_single_b210/README.md)
- [02 — RX-gain sweep with cable offset](02_dual_rx_channel_single_b210/README.md)
- [03 — single-B210 TX-gain sweep](03_dual_tx_channel_single_b210/README.md)
- [04 — two-dimensional RX-gain matrix](04_dual_rx_matrix_single_b210/README.md)
- [05 — clock/VCO-rate trace sweep](05_vco_rates/README.md)
- [06 — multi-USRP RX-gain sweep](06_multi_usrp_rx/README.md)
- [06 archived setup](06_multi_usrp_rx_old/README.md)
- [06 — type-2 splitter](06_multi_usrp_rx_splitter_type_2/README.md)
- [07 — multi-USRP phase stability](07_multi_usrp_rx_time/README.md)
- [07 archived setup](07_multi_usrp_rx_time_old/README.md)
- [08 — source-power/SNR sweep](08_multi_usrp_ideal_snr/README.md)
- [10 — archived dual-RX rerun](10_dual_rx_channel_single_b210/README.md)
- [20 — single-B210 external/internal loopback](20_loopback_single_b210/README.md)
- [21 — revised custom-FPGA loopback](21_loopback_single_b210/README.md)
- [22 — four-B210 loopback comparison](22_multi_usrp_loopback/README.md)
- [23 — four-B210 loopback RX-gain sweep](23_multi_usrp_loopback_rx_gain/README.md)
- [30 — multi-USRP synchronized output](30_mulit_usrp_sync_only_lb/README.md)
- [31 — synchronized output with phase offsets](31_mulit_usrp_sync_only_lb_add_phase/README.md)
- [32 — synchronized output with cable correction](32_mulit_usrp_sync_only_lb_clo/README.md)
- [33 — cable correction and phase offsets](33_mulit_usrp_sync_only_lb_clo_add_phase/README.md)
- [40 — local synchronization prototype](40_sync/README.md)
- [41 — pilot/loopback/transmission prototype](41_sync/README.md)
- [42 — internal-loopback synchronization prototype](42_sync/README.md)
- [XXX — archived synchronization template](XXX_mulit_usrp_sync_only_lb_clo/README.md)

## Historical experiment notes

The material below is the original lab notebook. Treat connection descriptions as experiment-specific; do not infer that gain, cable, or FPGA settings transfer to experiments 50–52.


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

This experiment consists of the following hardware components:
- rpi-T04 as transmitter (PPS + 10 MHz)
- RF splitter [ZC16PD-252-S+](https://www.minicircuits.com/pdfs/ZC16PD-252-S+.pdf)
- rpi-T05/rpi-T06/rpi-T07/rpi-T08 as receivers

One constant reference signal generated by USRP rpi-T04 with PPS + 10 MHz connected to the test octoclock.
Reference signal, connected to 4 USRPs via the RF splitter.

From the splitter 8 cables are connected to all RX channels of the four USRPs.

Gain of RX channel 1 constant en sweep in channel B gain

The following adjustments iq_capture_b210.py were made compare to exp e.g. 02
  - TX_A and TX_B removed
  - TX_CHANNELS removed
  - tune_usrp is simplified --> only rx instructions
  - tx_ref function is removed

More information and results about this experiement [here](https://github.com/techtile-by-dramco/NI-B210-Sync/tree/main/experiments/06_multi_usrp_rx).

<!-- **************************************************************************************************************************** -->
## 06_multi_usrp_rx_splitter_type_2

Same expirement als 06_multi_usrp_rx but with another RF splitter.
RF splitter [ZC16PD-252-S+](https://www.minicircuits.com/pdfs/ZC16PD-252-S+.pdf) used in "06_multi_usrp_rx" has PHASE UNBALANCE up to 18 degrees and it depends on the frequency band.

Therefore we used/made a more accurates splitter design.

More information and results about this experiement [here](https://github.com/techtile-by-dramco/NI-B210-Sync/tree/main/experiments/06_multi_usrp_rx_splitter_type_2).

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

<!-- **************************************************************************************************************************** -->
# Loopback experiments
<!-- **************************************************************************************************************************** -->
## 20_loopback_single_b210

With one USRP compare internal loopback with external loopback.

The .bin file used for the internal loopback "usrp_b210_fpga.bin" [see here](https://github.com/techtile-by-dramco/usrp/blob/main/fpga/usrp_b210_fpga.bin). This FPGA bin file is made by dramco.

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/20_loopback_single_b210/pictures/setup.jpg" width="200"></td>
    <td>
  
| ⚙️ Bash Settings   | Value | Unit |
|--------------|----------|-|
| TX_GAIN      | 38       | dB |
| GAIN_A       | 30       | dB |
| GAIN_B       | 30        | dB |
| ITERATIONS   | 10      | - |

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

- **Create csv file** Mount the whole RPI folder structure via Samba to your PC to do the processing locally.
  Mount RPI folder en parse the location of the raw data `W:\NI-B210-Sync\experiments\20_loopback_single_b210\client\rawdata`

```
python experiments\20_loopback_single_b210\processing\store_individual_phases.py --in-dir W:\NI-B210-Sync\experiments\20_loopback_single_b210\client\rawdata --out-dir experiments\20_loopback_single_b210\results
```

- **Create plots** plot_mean_3d
```
python .\experiments\20_loopback_single_b210\processing\plot_mean_std_angles.py --csv_file .\experiments\20_loopback_single_b210\results\circmean_and_circstd.csv
```

### Results [J]
<img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/20_loopback_single_b210/phase_difference_vs_time_with_variance.png" width="800">

<!-- **************************************************************************************************************************** -->
## 21_loopback_single_b210

With one USRP compare internal loopback with external loopback.

The .bin file used for the internal loopback "usrp_b210_fpga_loopback.bin" [see here](https://github.com/techtile-by-dramco/usrp/blob/main/fpga/usrp_b210_fpga_loopback.bin). This FPGA bin file is made by dramco.

Same experiment as 20_loopback_single_b210.

- **Create csv file** Mount the whole RPI folder structure via Samba to your PC to do the processing locally.
  Mount RPI folder en parse the location of the raw data `W:\NI-B210-Sync\experiments\20_loopback_single_b210\client\rawdata`

```
python experiments\21_loopback_single_b210\processing\store_individual_phases.py --in-dir W:\NI-B210-Sync\experiments\21_loopback_single_b210\client\rawdata --out-dir experiments\21_loopback_single_b210\results
```

- **Create plots** plot_mean_3d
```
python .\experiments\21_loopback_single_b210\processing\plot_mean_std_angles.py --csv_file .\experiments\21_loopback_single_b210\results\circmean_and_circstd.csv
```

### Results [J]
<img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/21_loopback_single_b210/phase_difference_vs_time_with_variance.png" width="800">

<!-- **************************************************************************************************************************** -->
## 22_multi_usrp_loopback

Four USRPs compare internal loopback with external loopback
Should give same phase difference since path is exactly the same.

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/22_multi_usrp_loopback/pictures/setup.jpg" width="200"></td>
    <td>
  
| ⚙️ Bash Settings   | Value | Unit |
|--------------|----------|-|
| TX_GAIN      | 38       | dB |
| GAIN_A       | 30       | dB |
| GAIN_B       | 30        | dB |
| ITERATIONS   | 50      | - |

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


- **Create csv file** Mount the whole RPI folder structure via Samba to your PC to do the processing locally.
  Mount RPI folder en parse the location of the raw data `W:\NI-B210-Sync\experiments\20_loopback_single_b210\client\rawdata`

```
python experiments\22_multi_usrp_loopback\processing\store_individual_phases.py --in-dir W:\NI-B210-Sync\experiments\22_multi_usrp_loopback\client\rawdata --out-dir experiments\22_multi_usrp_loopback\results
python experiments\22_multi_usrp_loopback\processing\store_individual_phases.py --in-dir X:\NI-B210-Sync\experiments\22_multi_usrp_loopback\client\rawdata --out-dir experiments\22_multi_usrp_loopback\results
python experiments\22_multi_usrp_loopback\processing\store_individual_phases.py --in-dir V:\NI-B210-Sync\experiments\22_multi_usrp_loopback\client\rawdata --out-dir experiments\22_multi_usrp_loopback\results
python experiments\22_multi_usrp_loopback\processing\store_individual_phases.py --in-dir U:\NI-B210-Sync\experiments\22_multi_usrp_loopback\client\rawdata --out-dir experiments\22_multi_usrp_loopback\results
```

- **Create plots** plot_mean_std_angles
```
python .\experiments\22_multi_usrp_loopback\processing\plot_mean_std_angles.py --csv_file .\experiments\22_multi_usrp_loopback\results\circmean_and_circstd.csv
```
### Results [J]
<img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/22_multi_usrp_loopback/phase_difference_vs_time_with_variance.png" width="800">

<!-- **************************************************************************************************************************** -->
## 23_multi_usrp_loopback_rx_gain

Same experiment as "22_multi_usrp_loopback" but just one iteration and a sweep in RX gain of channel B.

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/22_multi_usrp_loopback/pictures/setup.jpg" width="200"></td>
    <td>
  
| ⚙️ Bash Settings   | Value | Unit |
|--------------|----------|-|
| TX_GAIN      | 38       | dB |
| GAIN_A       | 30       | dB |
| GAIN_B_START | 7        | dB |
| GAIN_B_STOP  | 48       | dB |
| GAIN_STEP    | 1        | dB |
| ITERATIONS   | 1        | - |

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

- **Create csv file** Mount the whole RPI folder structure via Samba to your PC to do the processing locally.
  Mount RPI folder en parse the location of the raw data `W:\NI-B210-Sync\experiments\23_multi_usrp_loopback_rx_gain\client\rawdata`

```
python experiments\23_multi_usrp_loopback_rx_gain\processing\store_individual_phases.py --in-dir W:\NI-B210-Sync\experiments\23_multi_usrp_loopback_rx_gain\client\rawdata --out-dir experiments\23_multi_usrp_loopback_rx_gain\results
python experiments\23_multi_usrp_loopback_rx_gain\processing\store_individual_phases.py --in-dir X:\NI-B210-Sync\experiments\23_multi_usrp_loopback_rx_gain\client\rawdata --out-dir experiments\23_multi_usrp_loopback_rx_gain\results
python experiments\23_multi_usrp_loopback_rx_gain\processing\store_individual_phases.py --in-dir V:\NI-B210-Sync\experiments\23_multi_usrp_loopback_rx_gain\client\rawdata --out-dir experiments\23_multi_usrp_loopback_rx_gain\results
python experiments\23_multi_usrp_loopback_rx_gain\processing\store_individual_phases.py --in-dir U:\NI-B210-Sync\experiments\23_multi_usrp_loopback_rx_gain\client\rawdata --out-dir experiments\23_multi_usrp_loopback_rx_gain\results
```

- **Create plots** plot_mean_std_angles
```
python .\experiments\23_multi_usrp_loopback_rx_gain\processing\plot_mean_std_angles.py --csv_file .\experiments\23_multi_usrp_loopback_rx_gain\results\circmean_and_circstd.csv
```

<!-- **************************************************************************************************************************** -->
# Sync experiments
<!-- **************************************************************************************************************************** -->
## 30_sync

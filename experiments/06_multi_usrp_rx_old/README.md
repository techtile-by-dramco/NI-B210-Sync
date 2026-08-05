# Experiment 06 (archived setup) — multi-USRP RX-gain sweep

This archived predecessor feeds one common 920 MHz tone to both receive chains of four B210s and compares their gain-dependent CH0/CH1 phase. Result filenames identify the historical receiver set as T06–T09; confirm the physical labels before attempting to reproduce it.

## Connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| RADIOS["Source B210 and four receiver B210s"]
    HOSTS["Receiver hosts"] -->|"USB 3"| RXS["Historical receiver set<br/>results labelled T06–T09"]
    SRC["Source B210 CH0 TX/RX<br/>920 MHz CW"] --> ATT["Rated attenuation"] --> SPLIT["RF splitter<br/>at least 8 used outputs"]
    SPLIT -->|"two outputs per radio"| PORTS["Each receiver:<br/>CH0 RX2 and CH1 RX2"]
```

This directory lacks the later setup photographs and should be treated as archival. Keep all splitter outputs and cables fixed, verify source power at every RX input, and run `client/run_experiment.sh` separately on each receiver host.

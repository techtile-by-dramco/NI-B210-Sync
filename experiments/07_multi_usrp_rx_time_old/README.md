# Experiment 07 (archived setup) — multi-USRP phase stability over time

This is the archived predecessor of Experiment 07. The code performs the same fixed-gain, hourly dual-RX capture, but the surviving records do not identify the complete receiver-to-cable mapping.

## Connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| ALL["Source and four receiver B210s"]
    SRC["Source B210 CH0 TX/RX<br/>920 MHz CW"] --> ATT["Rated attenuation"] --> SPLIT["RF splitter<br/>8 outputs used"]
    SPLIT -->|"two fixed cables per receiver"| RXS["Four B210s:<br/>CH0 RX2 and CH1 RX2"]
```

Treat this directory as archival and confirm every tile/cable label from the raw-data filenames before reuse. The maintained topology description is in `../07_multi_usrp_rx_time/README.md`.

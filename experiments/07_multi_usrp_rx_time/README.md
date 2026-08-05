# Experiment 07 — multi-USRP phase stability over time

This experiment holds both RX gains at 38 dB and repeats four captures per hour for 100 hours. It reuses the common-tone, dual-RX topology of Experiment 06.

## Connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| ALL["T04 source and T05–T08 receivers"]
    T04["T04 CH0 TX/RX<br/>920 MHz CW"] --> ATT["Rated attenuation"] --> SPLIT["RF splitter<br/>8 outputs used"]
    SPLIT -->|"two fixed cables per tile"| RXS["T05–T08<br/>CH0 RX2 and CH1 RX2"]
    HOSTS["T05–T08 hosts"] -->|"USB 3"| RXS
```

Do not move the splitter or RF cables during the long run. Start the continuous T04 waveform described in the historical experiment notes, then run `client/run_experiment.sh` on every receiver. The shell script contains the hourly schedule.

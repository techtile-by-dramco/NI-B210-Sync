# Experiment 08 — source-power/SNR sweep

The intended experiment reuses the Experiment 06 splitter topology while sweeping the T04 transmit gain from 70 dB down to 50 dB. The current `run_experiment.sh` starts only the remote T04 waveform; its receiver-acquisition loops are commented out, so receiver captures must be started separately if this experiment is resumed.

## Connections

```mermaid
flowchart LR
    CTRL["Control host"] -->|"SSH"| T04HOST["T04 host"]
    T04HOST -->|"USB 3"| T04["T04 B210"]
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| ALL["T04 and T05–T08"]
    T04TX["T04 CH0 TX/RX<br/>920 MHz CW"] --> ATT["Rated attenuation"] --> SPLIT["RF splitter<br/>8 outputs used"]
    SPLIT -->|"two cables per tile"| RXS["T05–T08<br/>CH0 RX2 and CH1 RX2"]
```

Measure the highest-gain power at the splitter outputs before connecting the receivers. Review the commented receiver loops and the hard-coded T04 address in `client/run_experiment.sh`; as stored, the script is not a complete synchronized acquisition.

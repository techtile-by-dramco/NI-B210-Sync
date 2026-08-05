# Experiment 23 — four-B210 loopback RX-gain sweep

This uses the same four-radio external/internal comparison as Experiment 22 while sweeping CH1 RX gain. CH0 RX gain and both TX gains remain fixed.

## Connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz, four outputs"| REF["T05–T08 REF IN"]
    OCTO -->|"PPS, four outputs"| PPS["T05–T08 PPS IN"]
    HOSTS["T05–T08 hosts"] -->|"USB 3"| RADIOS["T05–T08 B210s<br/>custom loopback image"]
    TX0["Each tile CH0 TX/RX"] --> ATT["One 20 dB attenuator<br/>per tile"] --> RX0["Same tile CH0 RX2<br/>external loopback, fixed RX gain"]
    FPGA["Custom FPGA routing<br/>on each tile"] --> LB1["Same tile CH1 internal loopback<br/>RX gain swept"]
    DISC["All CH1 external RF connectors<br/>left unconnected"]
```

Keep the external-loop paths fixed during the sweep. Run `client/run_experiment.sh` on each participating tile; it sweeps CH1 RX gain from 7 to 48 dB.

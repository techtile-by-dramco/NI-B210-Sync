# Experiment 22 — external/internal loopback comparison on four B210s

This applies the Experiment 21 comparison to T05–T08. Every tile has one attenuated external loopback and one custom-FPGA internal loopback; the radios are not connected to one another at RF.

## Connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz, four outputs"| REF["T05–T08 REF IN"]
    OCTO -->|"PPS, four outputs"| PPS["T05–T08 PPS IN"]
    HOSTS["T05–T08 hosts"] -->|"USB 3"| RADIOS["T05–T08 B210s<br/>custom loopback image"]
    TX0["Each tile CH0 TX/RX"] --> ATT["One 20 dB attenuator<br/>per tile"] --> RX0["Same tile CH0 RX2<br/>external loopback"]
    FPGA["Custom FPGA routing<br/>on each tile"] --> LB1["Same tile CH1<br/>internal TX-to-RX loopback"]
    DISC["All CH1 external RF connectors<br/>left unconnected"]
```

Use four identical, labelled external-loop cables and verify attenuation separately on every tile. Run `client/run_experiment.sh` on each host; the stored script performs 50 fixed-gain repetitions.

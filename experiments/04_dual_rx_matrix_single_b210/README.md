# Experiment 04 — two-dimensional RX-gain matrix

This experiment sweeps both receive gains and records the CH0-minus-CH1 phase over the complete gain matrix. Its RF topology is the same dual external loopback used by Experiments 01–03.

## Connections

```mermaid
flowchart LR
    HOST["Host running client scripts"] -->|"USB 3"| B210["USRP B210"]
    OCTO["External reference source / OctoClock"] -->|"10 MHz"| REF["B210 REF IN"]
    OCTO -->|"PPS"| PPS["B210 PPS IN"]
    TX0["CH0 TX/RX"] --> ATT0["20 dB attenuator"] --> RX0["CH0 RX2<br/>RX gain A swept"]
    TX1["CH1 TX/RX"] --> ATT1["20 dB attenuator"] --> RX1["CH1 RX2<br/>RX gain B swept"]
```

Use fixed, labelled RF cables throughout the matrix; moving a cable changes the phase being attributed to gain. Run `client/run_experiment.sh`, then use the two- and three-dimensional plotting scripts in `processing/`.

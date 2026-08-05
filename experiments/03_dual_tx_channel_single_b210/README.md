# Experiment 03 — single-B210 TX-gain sweep

This experiment uses the same two external loopback paths as Experiment 02, but fixes both RX gains and sweeps the CH1 TX gain while CH0 TX gain remains fixed.

## Connections

```mermaid
flowchart LR
    HOST["Host running client scripts"] -->|"USB 3"| B210["USRP B210"]
    OCTO["External reference source / OctoClock"] -->|"10 MHz"| REF["B210 REF IN"]
    OCTO -->|"PPS"| PPS["B210 PPS IN"]
    TX0["CH0 TX/RX<br/>fixed TX gain"] --> ATT0["20 dB attenuator"] --> RX0["CH0 RX2"]
    TX1["CH1 TX/RX<br/>swept TX gain"] --> ATT1["20 dB attenuator"] --> RX1["CH1 RX2"]
```

Do not remove either attenuator during the sweep. Check the maximum configured gain against the B210 RX input limit before starting `client/run_experiment.sh`.

# Experiment 10 — duplicate single-B210 dual-RX sweep

The code is a near-duplicate of Experiment 01 and the surviving `setup-2.jpg` shows the unequal-cable topology used in Experiment 02. No separate historical objective is recorded, so treat this directory as an archived rerun rather than an independent setup.

## Connections

```mermaid
flowchart LR
    HOST["Host running client scripts"] -->|"USB 3"| B210["USRP B210"]
    OCTO["External reference source / OctoClock"] -->|"10 MHz"| REF["B210 REF IN"]
    OCTO -->|"PPS"| PPS["B210 PPS IN"]
    TX0["CH0 TX/RX"] --> ATT0["20 dB attenuator"] --> LONG["Longer cable"] --> RX0["CH0 RX2"]
    TX1["CH1 TX/RX"] --> ATT1["20 dB attenuator"] --> SHORT["Shorter cable"] --> RX1["CH1 RX2"]
```

Confirm the intended cable assignment from `setup-2.jpg` before reuse. The stored shell script fixes CH0 RX gain and sweeps CH1 RX gain.

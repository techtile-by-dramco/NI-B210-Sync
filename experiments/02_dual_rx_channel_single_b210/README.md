# Experiment 02 — RX-gain sweep with cable phase offset

This repeats Experiment 01 with deliberately unequal loopback cable lengths so that the two RX chains have a non-zero baseline phase difference. The setup photograph shows the longer path on CH0/A and the shorter path on CH1/B.

## Connections

```mermaid
flowchart LR
    HOST["Host running client scripts"] -->|"USB 3"| B210["USRP B210"]
    OCTO["External reference source / OctoClock"] -->|"10 MHz"| REF["B210 REF IN"]
    OCTO -->|"PPS"| PPS["B210 PPS IN"]
    TX0["CH0 TX/RX"] --> ATT0["20 dB attenuator"] --> LONG["Longer labelled cable"] --> RX0["CH0 RX2"]
    TX1["CH1 TX/RX"] --> ATT1["20 dB attenuator"] --> SHORT["Shorter labelled cable"] --> RX1["CH1 RX2"]
```

Keep the two labelled paths in the same orientation for the complete sweep. Verify safe TX-to-RX attenuation before running `client/run_experiment.sh`. The script fixes CH0 RX gain and sweeps CH1 RX gain at 920 MHz.

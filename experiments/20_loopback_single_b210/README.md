# Experiment 20 — external versus internal loopback on one B210

This experiment compares one externally cabled TX-to-RX path with the custom-FPGA internal loopback path on the other RF chain. The archived photograph shows the external loop on CH0/A and no external RF cable on CH1/B.

## Connections

```mermaid
flowchart LR
    HOST["Host running client scripts"] -->|"USB 3"| B210["USRP B210<br/>custom FPGA image"]
    OCTO["External reference source / OctoClock"] -->|"10 MHz"| REF["B210 REF IN"]
    OCTO -->|"PPS"| PPS["B210 PPS IN"]
    TX0["CH0 TX/RX"] --> ATT["20 dB attenuator"] --> RX0["CH0 RX2<br/>external loopback"]
    FPGA["Custom FPGA routing"] --> LB1["CH1 TX-to-RX<br/>internal loopback"]
    DISC["CH1 RF connectors<br/>no external cable"]
```

Verify the custom image in `client/usrp_b210_fpga.bin` and the channel mapping on one radio before relying on the comparison. The physical attenuator must remain in the CH0 external loop. Run `client/run_experiment.sh` for ten fixed-gain repetitions.

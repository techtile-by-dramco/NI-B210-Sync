# Experiment 21 — revised custom-FPGA loopback on one B210

This repeats Experiment 20 using `usrp_b210_fpga_loopback.bin`. It compares the photographed CH0/A external loopback against the internally routed CH1/B path.

## Connections

```mermaid
flowchart LR
    HOST["Host running client scripts"] -->|"USB 3"| B210["USRP B210<br/>usrp_b210_fpga_loopback.bin"]
    OCTO["External reference source / OctoClock"] -->|"10 MHz"| REF["B210 REF IN"]
    OCTO -->|"PPS"| PPS["B210 PPS IN"]
    TX0["CH0 TX/RX"] --> ATT["20 dB attenuator"] --> RX0["CH0 RX2<br/>external loopback"]
    FPGA["Custom FPGA routing"] --> LB1["CH1 TX-to-RX<br/>internal loopback"]
    DISC["CH1 RF connectors<br/>no external cable"]
```

Confirm the custom-image hash and verify both paths at low gain before collecting repetitions. Run `client/run_experiment.sh`; processing scripts compare the individual and relative phases.

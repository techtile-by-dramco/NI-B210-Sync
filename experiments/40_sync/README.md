# Experiment 40 — local synchronization/loopback prototype

This directory is a prototype rather than a fully documented bench experiment. The code loads `usrp_b210_fpga_loopback.bin`, activates both TX and RX channels, requires external 10 MHz/PPS, and performs a timed local capture. No historical RF connection table survives.

## Inferred connections

```mermaid
flowchart LR
    HOST["Host running iq_capture_b210.py"] -->|"USB 3"| B210["USRP B210<br/>custom loopback image"]
    OCTO["External reference source / OctoClock"] -->|"10 MHz"| REF["B210 REF IN"]
    OCTO -->|"PPS"| PPS["B210 PPS IN"]
    FPGA["Custom FPGA image"] --> LB["CH0 and CH1 timed<br/>TX/RX loopback capture"]
    RF["External RF ports"] -.->|"No cabled topology recorded"| CHECK["Confirm or disconnect<br/>before running"]
```

The diagram is an inference from the code, not a verified reconstruction. The script requires command-line experiment, measurement, gain, and TX-gain arguments but has no wrapper script. Confirm what the custom FPGA image routes before enabling either transmitter.

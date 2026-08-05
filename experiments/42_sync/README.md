# Experiment 42 — internal-loopback synchronization prototype

Experiment 42 is a debugging variant of Experiment 41. In the stored code, both `measure_pilot` and `measure_loopback` enable the same custom-FPGA CH1 loopback path. It therefore does not acquire an independent external pilot and cannot by itself validate end-to-end pilot calibration.

## Inferred connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| RADIOS["Participating B210s"]
    SERVER["ZMQ sync server"] <-->|"Ethernet control"| HOSTS["B210 client hosts"]
    REFGEN["Common 920 MHz RF reference"] --> REFSPLIT["RF splitter"] --> CH0["Every B210 CH0 RX2"]
    FPGA["Custom FPGA image"] --> LOOP["CH1 internal TX-to-RX path<br/>used for both stored measurements"]
    TXS["CH1 TX/RX outputs<br/>after loopback measurement"] --> ATTS["Rated attenuation"] --> SCOPE["Oscilloscope 50 Ω inputs"]
```

Treat this directory as an incomplete prototype. Verify that the RF reference is safely applied to CH0, disconnect external CH1 inputs during internal loopback, and record the tile-to-scope mapping before any output comparison.

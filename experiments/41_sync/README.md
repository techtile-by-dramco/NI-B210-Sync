# Experiment 41 — synchronized pilot, loopback calibration, and transmission prototype

This prototype coordinates one or more B210 clients through the ZMQ server. With `RX_TX_SAME_CHANNEL: true`, CH0 receives the common RF reference, CH1 receives an external pilot, CH1 is then internally looped back, and CH1 finally transmits with the calculated phase correction. The surviving scope image shows a two-radio comparison, but the exact tile-to-scope-channel mapping is not recorded.

## Stage 1 — pilot acquisition

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| RADIOS["Participating B210s"]
    SERVER["ZMQ sync server"] <-->|"Ethernet control"| HOSTS["B210 client hosts"]
    REFGEN["Common 920 MHz RF reference"] --> REFSPLIT["RF splitter"] --> CH0["Every B210 CH0 RX2"]
    PILOT["Common pilot source"] --> PILOTSPLIT["RF splitter / switch"] --> CH1RX["Every B210 CH1 TX/RX<br/>RX during pilot stage"]
```

## Stage 2 — internal loopback

```mermaid
flowchart LR
    FPGA["Custom FPGA image<br/>register 0 selects loopback"] --> LOOP["Each B210 CH1<br/>internal TX-to-RX loopback"]
    PILOT["Pilot branch"] --> TERM["DISCONNECTED and safely terminated"]
    OUT["CH1 external path"] -.->|"Keep isolated"| LOOP
```

## Stage 3 — phase-corrected output comparison

```mermaid
flowchart LR
    TXS["Participating B210<br/>CH1 TX/RX outputs"] --> ATTS["Rated attenuation<br/>one path per radio"] --> SCOPE["Oscilloscope 50 Ω inputs<br/>record tile/channel mapping"]
    SERVER["ZMQ sync server"] -->|"common start command"| TXS
```

These switching stages are inferred from the code and must not be hard-wired together without isolation: CH1 is reused for pilot reception and transmission. Confirm source protection, attenuation, and the intended participant count before running `server/sync-server.py` and the client wrapper.

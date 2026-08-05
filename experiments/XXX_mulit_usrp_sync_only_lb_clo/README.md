# XXX_mulit_usrp_sync_only_lb_clo — archived template

- clo = cable length offset

- Four USRPs are synchronized using the reference signal applied to the RX port of channel 0.
- The RX/TX port of channel 1 is connected to the oscilloscope.
- A total of 100 iterations are performed.
- During each synchronization cycle, the oscilloscope measures the phase relationship of channels 2, 3, and 4 with respect to channel 1.

## Inferred connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| RADIOS["Source plus four B210s"]
    SERVER["ZMQ sync server"] <-->|"Ethernet"| HOSTS["Four client hosts"]
    SRC["920 MHz reference source"] --> ATT["Rated attenuation"] --> S1["2-way splitter 1"]
    S1 --> S2A["2-way splitter 2A"]
    S1 --> S2B["2-way splitter 2B"]
    S2A --> C12["Two labelled reference cables"] --> REF12["Two radios CH0 RX2"]
    S2B --> C34["Two labelled reference cables"] --> REF34["Two radios CH0 RX2"]
    FPGA["Custom FPGA loopback"] --> LB["Each radio CH1<br/>internal TX-to-RX calibration"]
    TXS["Four CH1 TX/RX outputs"] -->|"rated paths;<br/>record mapping"| SCOPE["Oscilloscope CH1–CH4<br/>50 Ω"]
```

This is an incomplete template derived from the related Experiment 30–33 code. Confirm the source tile, cable-phase file, client count, and scope mapping before reuse.

### Results [raw & abs(raw)]

<table>
  <tr>
    <td><img src="" width="600"></td>
    <td><img src="" width="600"></td>
  </tr>
</table>

### Results [between outputs same 2-way splitter & between outputs different 2-way splitters]

<table>
  <tr>
    <td><img src="" width="600"></td>
    <td><img src="" width="600"></td>
  </tr>
</table>

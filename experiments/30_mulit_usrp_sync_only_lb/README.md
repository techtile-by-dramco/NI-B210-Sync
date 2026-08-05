# 30_mulit_usrp_sync_only_lb

One testtile that transmit a sine wave
```
python3 examples/tx_waveforms.py  --args "type=b200" --freq 920e6 --rate 1e6 --duration 1e8 --channels 0 --wave-freq 0e5 --wave-ampl 0.8 --gain 70
```

- Four USRPs are synchronized using the reference signal applied to the RX port of channel 0.
- The RX/TX port of channel 1 is connected to the oscilloscope.
- A total of 100 iterations are performed.
- During each synchronization cycle, the oscilloscope measures the phase relationship of channels 2, 3, and 4 with respect to channel 1.

## Connections

```mermaid
flowchart LR
    OCTO["Common OctoClock"] -->|"10 MHz and PPS<br/>separate outputs"| RADIOS["T04 and T05–T08"]
    SERVER["ZMQ sync server"] <-->|"Ethernet"| HOSTS["T05–T08 client hosts"]
    T04["T04 CH0 TX/RX<br/>920 MHz CW"] --> ATT["20 dB attenuator"] --> S1["2-way splitter 1"]
    S1 --> S2A["2-way splitter 2A"]
    S1 --> S2B["2-way splitter 2B"]
    S2A -->|"two fixed cables"| REF12["Two radios CH0 RX2"]
    S2B -->|"two fixed cables"| REF34["Two radios CH0 RX2"]
    FPGA["Custom FPGA loopback"] --> LB["Each radio CH1<br/>internal TX-to-RX calibration"]
    TXS["T05–T08 CH1 TX/RX"] -->|"four rated paths;<br/>preserve recorded mapping"| SCOPE["Oscilloscope CH1–CH4<br/>50 Ω"]
```

The surviving files do not unambiguously record which tile was assigned to each scope channel. Preserve the historical cable labels when analyzing old data, and explicitly record the mapping before a rerun.

### Results [raw & abs(raw)]

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/30_mulit_usrp_sync_only_lb/scope_phases.png" width="600"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/30_mulit_usrp_sync_only_lb/scope_phases_abs.png" width="600"></td>
  </tr>
</table>

### Results [between outputs same 2-way splitter & between outputs different 2-way splitters]

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/30_mulit_usrp_sync_only_lb/scope_phases_same_splitter.png" width="600"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/30_mulit_usrp_sync_only_lb/scope_phases_different_splitter.png" width="600"></td>
  </tr>
</table>

### Conclusion

That script to measure the phase differences is not good and requires an update.

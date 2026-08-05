# 31_mulit_usrp_sync_only_lb_add_phase

- One testtile that transmit a sine wave
```
python3 examples/tx_waveforms.py  --args "type=b200" --freq 920e6 --rate 1e6 --duration 1e8 --channels 0 --wave-freq 0e5 --wave-ampl 0.8 --gain 70
```
- Four USRPs are synchronized using the reference signal applied to the RX port of channel 0.
- The RX/TX port of channel 1 is connected to the oscilloscope.
- A total of 100 iterations are performed.
- During each synchronization cycle, the oscilloscope measures the phase relationship of channels 2, 3, and 4 with respect to channel 1.
- The build-in measurement functie is used to measure the phases.
- To prevent incorrect phase results, additional **phase offsets** were added: T05: 0°, T06: 45°, T07: 90°, and T08: 135°.

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
    PHASE["Software TX offsets<br/>T05 0°, T06 45°<br/>T07 90°, T08 135°"] --> TXS["T05–T08 CH1 TX/RX"]
    TXS -->|"one rated path per tile;<br/>record mapping"| SCOPE["Oscilloscope CH1–CH4<br/>50 Ω"]
```

The phase offsets are software settings, not extra cable sections. Confirm and record the tile-to-scope-channel mapping before collecting data.

<img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/31_mulit_usrp_sync_only_lb_add_phase/pictures/circuit-setup.png" width="1000">
Before splitter 1 is a 20 dB attentuator

### Results [raw & phase offset removed]

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/31_mulit_usrp_sync_only_lb_add_phase/scope_phases.png" width="600"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/31_mulit_usrp_sync_only_lb_add_phase/scope_phases_offset_removed.png" width="600"></td>
  </tr>
</table>

| Channels     | Mean                 | Std                  |
|--------------|----------------------|-----------------------|
| CH1 - CH2    | 0.5744586887005192   | 0.9478001175555331    |
| CH1 - CH3    | 7.081923336931293    | 0.9869667338113204    |
| CH1 - CH4    | 7.959343748393683    | 0.9218934521364133    |

### Conclusion

- The update procedure (script) to measure phase relations with the scope is solved in this experiment.
- We can again observe that the outputs of the 2-way splitters exhibit a very good phase relationship. 
- As a result, the phase relationship between CH1–CH2 and CH3–CH4 yields very good results. 
- Consequently, CH1–CH3, CH1–CH4, CH2–CH3, and CH2–CH4 produce less accurate phase results.

⚠️ Here, the phase was always measured relative to CH1, in the following way:
CH1 − CH2, CH1 − CH3, CH1 − CH4.

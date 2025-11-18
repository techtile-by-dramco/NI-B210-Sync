# 31_mulit_usrp_sync_only_lb_add_phase

- Four USRPs are synchronized using the reference signal applied to the RX port of channel 0.
- The RX/TX port of channel 1 is connected to the oscilloscope.
- A total of 100 iterations are performed.
- During each synchronization cycle, the oscilloscope measures the phase relationship of channels 2, 3, and 4 with respect to channel 1.
- The build-in measurement functie is used to measure the phases.
- To prevent incorrect phase results, additional **phase offsets** were added: T05: 0°, T06: 45°, T07: 90°, and T08: 135°.

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

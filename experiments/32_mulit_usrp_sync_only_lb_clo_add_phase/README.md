# 32_mulit_usrp_sync_only_lb_clo_add_phase

clo = cable length offset

- Four USRPs are synchronized using the reference signal applied to the RX port of channel 0.
- **HERE THERE ARE ADDITIONAL PHASE OFFSETS BETWEEN THE REFERENCE SIGNALS**
- The RX/TX port of channel 1 is connected to the oscilloscope.
- A total of 100 iterations are performed.
- During each synchronization cycle, the oscilloscope measures the phase relationship of channels 2, 3, and 4 with respect to channel 1.
- The build-in measurement functie is used to measure the phases.
<!--
- To prevent incorrect phase results, additional **phase offsets** were added: T05: 0°, T06: 45°, T07: 90°, and T08: 135°.
-->

⚠️⚠️⚠️ To make this work, it is essential that the phase differences between the reference cables are measured with respect to one common reference, and then applied in the following way: CH2 − CH1, CH3 − CH1, CH4 − CH1. ⚠️⚠️⚠️


### Results [raw & phase offset removed]

<table>
  <tr>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/32_mulit_usrp_sync_only_lb_clo_add_phase/scope_phases.png" width="600"></td>
  </tr>
</table>

| Channels     | Mean                 | Std                   |
|--------------|----------------------|-----------------------|
| CH1 - CH2    | 356.3714863358002    | 4.816954229930222     |
| CH1 - CH3    | 352.21435685845887   | 0.8243882873109306    |
| CH1 - CH4    | 352.3985647368154    | 0.9102381400101058    |

### Conclusion

We can again observe that the outputs of the 2-way splitters exhibit a very good phase relationship. 
As a result, the phase relationship between CH1–CH2 and CH3–CH4 yields very good results. 
Consequently, CH1–CH3, CH1–CH4, CH2–CH3, and CH2–CH4 produce less accurate results.

⚠️ Here, the phase was always measured relative to CH1, in the following way: CH2 − CH1, CH2 − CH1, CH3 − CH1.

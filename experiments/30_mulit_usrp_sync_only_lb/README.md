# 30_mulit_usrp_sync_only_lb

- Four USRPs are synchronized using the reference signal applied to the RX port of channel 0.
- The RX/TX port of channel 1 is connected to the oscilloscope.
- A total of 100 iterations are performed.
- During each synchronization cycle, the oscilloscope measures the phase relationship of channels 2, 3, and 4 with respect to channel 1.

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
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/30_mulit_usrp_sync_only_lb/scope_phases_same_plitter.png" width="600"></td>
    <td><img src="https://github.com/techtile-by-dramco/NI-B210-Sync/blob/main/experiments/30_mulit_usrp_sync_only_lb/scope_phases_different_plitter.png" width="600"></td>
  </tr>
</table>

# Experiment 05 — B210 clock/VCO-rate trace sweep

This is a configuration-only experiment. It opens one B210, sweeps the master-clock rate, tunes the receiver to 917 MHz, and parses UHD trace output for BBPLL/VCO and divider settings. No RF stimulus is captured.

## Connections

```mermaid
flowchart LR
    HOST["Host with UHD Python<br/>and trace logging"] -->|"USB 3"| B210["USRP B210"]
    RF["RF ports"] -.->|"No signal required;<br/>disconnect or terminate"| TERM["50 Ω terminations"]
```

The code does not select an external clock or PPS source, so none is required for reproducing the logged-rate sweep. Run `python3 sweep_rates.py`; it writes `uhd_debug_trace.log` and `clock_tuning_summary.csv` in this directory.

# Shared T05–T08 experiment code

This package is used by experiments 50–52. It provides YAML validation, the continuous T04 RF-source launcher, the manuscript correlation estimator, circular statistics, event interventions, JSONL result writing, the UHD B210 adapter, the four-node JSON protocol, and MSO64B waveform power/phase processing.

Install the ordinary Python dependencies with:

```bash
python3 -m pip install -r experiments/t05_t08_common/requirements.txt
```

The `uhd` Python module is supplied by the NI/Ettus UHD installation and is intentionally not a pip requirement. Analysis and every `--dry-run` command work without UHD; hardware acquisition fails early with a targeted message if the binding is unavailable.

For every 5X experiment, T04 CH0 `TX/RX` is the RF source and T05–T08 are the devices under test. Start the source on T04 with the applicable experiment configuration:

```bash
python3 experiments/t05_t08_common/run_t04_source.py \
  --config experiments/50_t05_t08_state_characterization/config.yml \
  --tx-gain-db 0
```

T04 is tuned to `center_frequency_hz` and transmits the configured complex-baseband tone, so the default RF output is 920.001 MHz. A hardware run requires an explicit TX gain and a measured `rf_source_output_attenuation_db`; verify safe power at every destination before transmitting. The launcher uses the installed/default FPGA and external 10 MHz/PPS, and should remain open and tuned for a complete measurement pass.

Phase conventions are fixed across all three experiments:

- `estimate_relative_phase(reference, observed)` returns \(R-O\), wrapped to ±π;
- `reference_cable_phase_deg` is manuscript \(\varphi_{cable,i}\), measured relative to the selected reference cable; and
- the narrowband correction is \((R-P)+(R-L)-2\varphi_{cable,i}\).

Do not change these signs in an experiment-specific script. If a measurement instrument uses the opposite channel subtraction, convert it when entering the cable calibration and record that conversion in the run notes.

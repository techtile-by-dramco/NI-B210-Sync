This folder contains scripts and results to investigate the phase stability and coherency of the B210 for multi-device phase-coherent operation.


## 01_dual_rx_channel_single_b210

In this experiment, a single B210 is used. The RX and TX channels are connected with an SMA cable and a 20 dB attenutator.
The goal is to determine the effect of RX gain configuration on the phase difference between the two channels.
Given that using one B210 ensures phase-coherency between the channels, we can see when a phase differences changes based on the gain index.

In the first setup, the setup ensured as equal path lengths as possible by using the same cables and attenutator.
In the 2nd setup a longer cable is connected to A/B. This induces an additional phase difference between the two channels. This was done intentionally as small IQ values could result in phase differences close to zero. 




### Keep the RX gains contast and change 1 TX Gain
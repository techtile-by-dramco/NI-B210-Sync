This folder contains scripts and results to investigate the phase stability and coherency of the B210 for multi-device phase-coherent operation.


## 01_dual_rx_channel_single_b210

In this experiment, a single B210 is used. The RX and TX channels are connected with an SMA cable and a 20 dB attenutator.
The goal is to determine the effect of RX gain configuration on the phase difference between the two channels.
Given that using one B210 ensures phase-coherency between the channels, we can see when a phase differences changes based on the gain index.

In the first setup, the setup ensured as equal path lengths as possible by using the same cables and attenutator.
In the 2nd setup a longer cable is connected to A/B. This induces an additional phase difference between the two channels. This was done intentionally as small IQ values could result in phase differences close to zero. 




### 02_dual_rx_channel_single_b210

Same as 01 but with setup 2 (ie one cable is longer than the other to induce an additional phase shift between the two RX-TX chains)


### 03_dual_tx

Same as 02 but now the RX gains are fixed and the TX gains are varied.


### 04

Same as 02 but now both the RX A and RX B are varied, yielding a matrix of phase differences


### 05

Scripts to extract relevant rates and configuration from trace logging.


### 06 

Fixed RX gains

4 USRPs are connected to one splitter with equal length cables. Phase differences are checked on the scope and they were aligned <1°. 


# Reciprocity calibration RX and TX PLL of USRP B210
**STEPS TO FOLLOW**

Problem: It is not possible to **transmit phase coherent signals** with different individual USRPs.
Reason: PLLs lock is not constant in time (Even if NI Clock Distribution Devices CDA-2990, the problem can not be solved.) 

Assumptions

synchronisattion overview

Purpose is to generate two sine waves that are in phase when pilot signal was received on both input channels.

# STEP 1. Proof the "phase coherency" problem

## 1.1. START with one USRP

### 1.1.1. Phase relation between two transmit channels of same USRP
- Generating two signals on the same USRP (e.g., 400 MHz signals) without coded phase shifts.
- MEASURE outputs TX-1 (USRP-1) and TX-2 (USRP-1) connected to a scope and visualize phase relation.

<span style="color:red">PHOTO</span>

### 1.1.2. Check the adaptability of the phase relation between the two channels on same USRP
- Similarly, generate two signals know with relative phase shift (e.g. 90°).
- MEASURE outputs TX-1 (USRP-1) and TX-2 (USRP-1) connected to a scope and visualize phase relation.
- Does the result correspond to the configured phase relationship?

PHOTO

## 1.2. MEASUREMENTs two USRPs

# STEP 2. Measure phase difference of internal RF-PLLs 
The purpose is to measure the phase difference between the RX RF-PLL ans the TX RF-PLL. 
- Start to lock the USRP RX and TX RF-PLL on the same frequency $f$.
- This measurement requires a physical 50 ohm SMA cable connection between RX-1 and TX-1 of the USRP.
- The measured phase difference will contain the sum of several components.

Signal representation of at the input and output of the USRP channels <br>
* Transmit signal $tx_1(t) = \exp(j2\pi ft) \cdot \exp(\phi_{tx,configured}) \cdot \exp(\phi_{pll,tx}) \cdot \exp(\phi_{L,tx})$
* Receive signal $rx_1(t) = \exp(j2\pi ft) \cdot \exp(\phi_{rx,configured}) \cdot \exp(\phi_{pll,rx}) \cdot \exp(\phi_{L,rx})$ <br>
With: <br>
  - $tx_1(t)$ and $rx_1(t)$ the signals transmitted or received at the SMA ports of the USRP.
  - $\phi_{tx,configured}$ and $\phi_{rx,configured}$ is the configured and recieved phases respectively.
  - $\phi_{L,rx}$ and $\phi_{L,rx}$ is the RF path between SMA connector port and RF transceiver IC.
  - $\phi_{pll,tx}$ and $\phi_{pll,rx}$ the initial absolute PLL phase realtive to some reference.

<!-- Multiplying transmit signal $tx_1(t)$ with receive signal $rx_1(t)$ gives the phase shift introduced by the SMA cable. -->
The received signal is the sum of the transmitted signal and the phase shift occured in the SMA cable.
$$rx_1(t) = tx_1(t) \cdot \exp(\phi_{SMA,cable})$$

$$\exp(j2\pi ft) \cdot \exp(\phi_{tx,configured}) \cdot \exp(\phi_{pll,tx}) \cdot \exp(\phi_{L,tx}) = \exp(j2\pi ft) \cdot \exp(\phi_{rx,configured}) \cdot \exp(\phi_{pll,rx}) \cdot \exp(\phi_{L,rx}) \cdot \exp(\phi_{SMA,cable})$$

<!-- \begin{equation}
\phi_{RX2} = \Delta\phi 
\end{equation}
$$ -->

This can be seen as the calibration procedure.
After this step, the PLL may not by 


## 2.1. 





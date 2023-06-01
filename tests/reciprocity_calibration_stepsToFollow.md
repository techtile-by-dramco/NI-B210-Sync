# Reciprocity calibration USRP RX and TX PLL: Steps to follow

Problem: It is not possible to **transmit phase coherent signals** with different individual USRPs.
Reason: PLLs lock is not constant in time (Even if NI Clock Distribution Devices CDA-2990, the problem can not be solved.) 

Purpose is to generate two sine waves that are in phase when pilot signal was received on both input channels.

# STEP 1: Finding and proof the "phase coherency" problem

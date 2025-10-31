#!/bin/bash

# Define the parameters
TX_GAIN=38        # Fixed TX gain
GAIN_A=30         # Fixed RX gain for A (CH0)
GAIN_B=30         # Fixed RX gain for A (CH0)
# GAIN_B_START=30 # Starting value for RX gain B
# GAIN_B_STOP=31  # Ending value for RX gain B
GAIN_STEP=1       # Step size for RX gain B
ITERATIONS=50     # Number of iterations per gain value

# Experiment and measurement identifiers
EXP_ID="exp_test"
# MEAS_ID=1


for ((i=1; i<=ITERATIONS; i++))
    do
        echo "Running iteration $i with RX gain B = $GAIN_B"
        python3 iq_capture_b210.py --exp $EXP_ID --meas $i --tx_gain $TX_GAIN --gain_a $GAIN_A --gain_b $GAIN_B
done

#!/bin/bash

# Define the parameters
TX_GAIN=38        # Fixed TX gain
GAIN_A=30         # Fixed RX gain for A (CH0)
GAIN_B_START=7    # Starting value for RX gain B
GAIN_B_STOP=55    # Ending value for RX gain B
GAIN_STEP=1       # Step size for RX gain B
ITERATIONS=100      # Number of iterations per gain value

# Experiment and measurement identifiers
EXP_ID="exp_test"
MEAS_ID=1


for ((i=1; i<=ITERATIONS; i++))
    do
    # Loop through the RX gain B values
    for ((GAIN_B=$GAIN_B_START; GAIN_B<=$GAIN_B_STOP; GAIN_B+=$GAIN_STEP))
    do
        echo "Running iteration $i with RX gain B = $GAIN_B"
        # Call the Python script with the current parameters
        python3 iq_capture_b210.py --exp $EXP_ID --meas $MEAS_ID --tx_gain $TX_GAIN --gain_a $GAIN_A --gain_b $GAIN_B
    done
done

#!/bin/bash

# Define the parameters
GAIN=38       # Step size for RX gain B
ITERATIONS=100      # Number of iterations per gain value

# Experiment and measurement identifiers
EXP_ID="exp_test"
MEAS_ID=1


for ((i=1; i<=ITERATIONS; i++))
    do
    for ((i=1; i<=4; i++))
        do
        echo "Running iteration $i with RX gain B = $GAIN"
        # Call the Python script with the current parameters
        python3 iq_capture_b210.py --exp $EXP_ID --meas $MEAS_ID --gain_a $GAIN --gain_b $GAIN
        sleep 5  # Waits 5 seconds.
    done
    sleep 3600  # Waits 5 seconds.
done

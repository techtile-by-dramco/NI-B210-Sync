#!/bin/bash

# Define the parameters
GAIN_TX_START=70
GAIN_TX_STOP=50
GAIN_A=30         # Fixed RX gain for A (CH0)
GAIN_B_START=7    # Starting value for RX gain B
GAIN_B_STOP=48    # Ending value for RX gain B
GAIN_STEP=1       # Step size for RX gain B
ITERATIONS=2      # Number of iterations per gain value


# Experiment and measurement identifiers
EXP_ID="exp_test"
MEAS_ID=1

# HOSTT05 = RPI-T08.local

HOST_T04 = "192.108.1.82"


for ((GAIN_TX=GAIN_TX_START; GAIN_TX<=GAIN_TX_STOP; GAIN_TX+=GAIN_STEP)); do
    echo "Running with TX gain = $GAIN_TX"
    ssh pi@$HOST_T04 "python3 examples/tx_waveforms.py \
        --args 'type=b200' \
        --freq 920e6 \
        --rate 1e6 \
        --duration 60 \
        --channels 0 \
        --wave-freq 0e5 \
        --wave-ampl 0.8 \
        --gain $GAIN_TX"
done

# for ((i=1; i<=ITERATIONS; i++))
#     do
#     # Loop through the RX gain B values
#     for ((GAIN_B=$GAIN_B_START; GAIN_B<=$GAIN_B_STOP; GAIN_B+=$GAIN_STEP))
#     do
#         echo "Running iteration $i with RX gain B = $GAIN_B"
#         # Call the Python script with the current parameters
#         python3 iq_capture_b210.py --exp $EXP_ID --meas $MEAS_ID --gain_a $GAIN_A --gain_b $GAIN_B
#     done
# done

# MEAS_ID=2
# # same but with same RX gain now
# for ((i=1; i<=ITERATIONS; i++))
#     do
#     # Loop through the RX gain B values
#     for ((GAIN_B=$GAIN_B_START; GAIN_B<=$GAIN_B_STOP; GAIN_B+=$GAIN_STEP))
#     do
#         echo "Running iteration $i with RX gain B = $GAIN_B"
#         # Call the Python script with the current parameters
#         python3 iq_capture_b210.py --exp $EXP_ID --meas $MEAS_ID --gain_a $GAIN_B --gain_b $GAIN_B
#     done
# done

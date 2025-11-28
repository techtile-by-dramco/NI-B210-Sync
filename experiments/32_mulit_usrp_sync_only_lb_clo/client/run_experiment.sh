#!/bin/bash

# Define the parameters
ITERATIONS=100       # Number of iterations per gain value

for ((i=1; i<=ITERATIONS; i++))
    do
        echo "Running iteration $i"
        python3 usrp-cal-bf.py
        echo "Sleeping 1 seconds before next iteration..."
        sleep 1

done

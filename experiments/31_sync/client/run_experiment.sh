#!/bin/bash

# Define the parameters
ITERATIONS=1       # Number of iterations per gain value

for ((i=1; i<=ITERATIONS; i++))
    do
        echo "Running iteration $i"
        python3 usrp-cal-bf.py
done

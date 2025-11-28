#!/usr/bin/python3
# usage: sync_server.py <delay> <num_subscribers>

# VALUE "num_subscribers" --> IMPORTANT --> The server waits until all subscribers have sent their "alive" or ready message before starting a measurement.

import zmq
import time
import sys
import os
from datetime import datetime
from helper import *

# =============================================================================
#                           Experiment Configuration
# =============================================================================
host = "*"               # Host address to bind to. "*" means all available interfaces.
sync_port = "5557"       # Port used for synchronization messages.
alive_port = "5558"      # Port used for heartbeat/alive messages.
data_port = "5559"       # Port used for data transmission.
# =============================================================================
# =============================================================================

if len(sys.argv) > 1:
    delay = int(sys.argv[1])
    num_subscribers = int(sys.argv[2])
else:
    delay = 2
    num_subscribers = 4

# Creates a socket instance
context = zmq.Context()

sync_socket = context.socket(zmq.PUB)
# Binds the socket to a predefined port on localhost
sync_socket.bind("tcp://{}:{}".format(host, sync_port))

# Create a SUB socket to listen for subscribers
alive_socket = context.socket(zmq.REP)
alive_socket.bind("tcp://{}:{}".format(host, alive_port))

# Create a SUB socket to listen for subscribers
data_socket = context.socket(zmq.REP)
data_socket.bind("tcp://{}:{}".format(host, data_port))

# Measurement and experiment identifiers
meas_id = 0

# Unique ID for the experiment based on current UTC timestamp
unique_id = str(datetime.utcnow().strftime("%Y%m%d%H%M%S"))

# Directory where this script is located
# script_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))

# ZeroMQ poller setup
poller = zmq.Poller()
poller.register(alive_socket, zmq.POLLIN)  # Register the alive socket to monitor incoming messages

# Track time of the last received message
new_msg_received = 0
# Maximum time to wait for messages before breaking out of the inner loop (10 minutes)
WAIT_TIMEOUT = 60.0 * 10.0

# Inform the user that the experiment is starting
print(f"Starting experiment: {unique_id}")

# Path to save the experiment data as a YAML file
current_file_path = os.path.abspath(__file__) 
current_dir = os.path.dirname(current_file_path)
parent_path = os.path.dirname(current_dir)
output_path = os.path.join(parent_path, f"data/exp-{unique_id}.yml")

with open(output_path, "w") as f:
    # Write experiment metadata to the YAML file
    f.write(f"experiment: {unique_id}\n")
    f.write(f"num_subscribers: {num_subscribers}\n")
    f.write(f"measurments:\n")

    while True:
        # Wait for all subscribers to send a message
        print(f"Waiting for {num_subscribers} subscribers to send a message...")
        
        # Start a new measurement entry in the YAML file
        f.write(f"  - meas_id: {meas_id}\n")
        f.write("    active_tiles:\n")

        # Track number of messages received from subscribers
        messages_received = 0
        start_processing = None

        while messages_received < num_subscribers:
            # Poll the socket for incoming messages with a 1-second timeout
            socks = dict(poller.poll(1000))

            # If some messages were received but no new message comes within WAIT_TIMEOUT, break
            if messages_received > 2 and time.time() - new_msg_received > WAIT_TIMEOUT:
                break

            if alive_socket in socks and socks[alive_socket] == zmq.POLLIN:
                # Record time when a new message is received
                new_msg_received = time.time()

                # Receive the message string from the subscriber
                message = alive_socket.recv_string()
                messages_received += 1

                # Print received message and write it to the YAML file
                print(f"{message} ({messages_received}/{num_subscribers})")
                f.write(f"     - {message}\n")

                # Process the request (example placeholder)
                response = "Response from server"

                # Send response back to the subscriber
                alive_socket.send_string(response)

        # Wait a fixed delay before sending the next SYNC signal
        print(f"sending 'SYNC' message in {delay}s...")
        f.flush()
        time.sleep(delay)

        # Increment measurement ID for next iteration
        meas_id += 1

        # Broadcast synchronization message to all subscribers
        sync_socket.send_string(f"{meas_id} {unique_id}")  # str(meas_id)
        print(f"SYNC {meas_id}")


        # *** EXTENSION *** JVM

        # Wait for all subscribers to send a TX MODE message
        print(f"Waiting for {num_subscribers} subscribers to send a TX Mode ...")

        # Track number of messages received from subscribers
        messages_received = 0
        start_processing = None

        while messages_received < num_subscribers:
            # Poll the socket for incoming messages with a 1-second timeout
            socks = dict(poller.poll(1000))

            # If some messages were received but no new message comes within WAIT_TIMEOUT, break
            if messages_received > 2 and time.time() - new_msg_received > WAIT_TIMEOUT:
                break

            if alive_socket in socks and socks[alive_socket] == zmq.POLLIN:
                # Record time when a new message is received
                new_msg_received = time.time()

                # Receive the message string from the subscriber
                message = alive_socket.recv_string()
                messages_received += 1

                # Print received message and write it to the YAML file
                print(f"{message} ({messages_received}/{num_subscribers})")

                # Process the request (example placeholder)
                response = "Response from server"

                # Send response back to the subscriber
                alive_socket.send_string(response)

        print(f"Wait 10s ...")

        time.sleep(10)

        print(f"Measure phases")

        save_phases()
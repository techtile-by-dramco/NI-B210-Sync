#!/usr/bin/python3

# simple_pub.py
import zmq
import time
from datetime import datetime, timezone


host = "*"
port = "5557"

# Creates a socket instance
context = zmq.Context()


start_socket = context.socket(zmq.PUB)
# Binds the socket to a predefined port on localhost
start_socket.bind("tcp://{}:{}".format(host, port))


hello_socket = context.socket(zmq.REP)
hello_socket.bind("tcp://*:5555")


while(True):
	message = hello_socket.recv()
	print(f"Node #{message.decode()} is ready")
	hello_socket.send_string("OK")

	message = hello_socket.recv()
	print(f"Node #{message.decode()} is ready")
	hello_socket.send_string("OK")


	# start_ms = datetime.now(timezone.utc).timestamp()
	# print(f"Waiting 30 seconds before starting the SYNC")

	# while(start_ms + 5*1000 > datetime.now(timezone.utc).timestamp()):
	#     try:
	#         message = hello_socket.recv(flags=zmq.NOBLOCK)
	#         print(f"Node #{message.decode()} is ready")
	#         hello_socket.send_string("OK")
	#     except zmq.ZMQError as e:
	#         if e.errno == zmq.EAGAIN:
	#             pass # no message was ready (yet!)
	#         else:
	#             traceback.print_exc()

	time.sleep(2)


# Sends a string message
start_socket.send_string("SYNC")
print("SYNC")


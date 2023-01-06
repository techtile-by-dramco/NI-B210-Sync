# simple_pub.py
import zmq
import time

host = "*"
port = "5557"

# Creates a socket instance
context = zmq.Context()


start_socket = context.socket(zmq.PUB)
# Binds the socket to a predefined port on localhost
start_socket.bind("tcp://{}:{}".format(host, port))


hello_socket = context.socket(zmq.REP)
hello_socket.bind("tcp://*:5555")

message = hello_socket.recv()
print(f"Node #{message} is ready")
hello_socket.send_string("OK")

message = hello_socket.recv()
print(f"Node #{message} is ready")
hello_socket.send_string("OK")


time.sleep(10)


# Sends a string message
start_socket.send_string("SYNC")
print("SYNC")

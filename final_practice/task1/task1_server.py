import math
import os
from socket import socket, AF_INET, SOCK_DGRAM, timeout
import sys
import time
import re
import json

SERVER_IP = "0.0.0.0"
PORT = 50000

class RR:
    def __init__(self):
        self.data_base = {}

    def put(self, type, key, value):
        self.data_base[type] = {key: value}

    def get(self, type, key):
        try:
            return self.data_base[type][key]
        except KeyError:
            return "NXDOMAIN"

if __name__ == "__main__":
    with socket(AF_INET, SOCK_DGRAM) as server_socket:
        server_socket.bind(("0.0.0.0", PORT))
        server_socket.settimeout(5)
        print(f'Server: Listening on {SERVER_IP}:{PORT}')
        rr = RR()
        rr.put("A", "example.com", "1.2.3.4")
        rr.put("PTR", "1.2.3.4", "example.com")
        try:
            while True:
                try:
                    data, addr = server_socket.recvfrom(1024)
                    query = data.decode()
                    print(f"Client: {query}")
                    query_dict = json.loads(data)
                    value = rr.get(query_dict["type"], query_dict["key"])
                    packet = json.dumps({"type": query_dict["type"], "key": query_dict["key"], "value": value})
                    if value == "NXDOMAIN":
                        print("Server: Record not found. Sending error.")
                    else:
                        print("Server: Record found. Sending answer.")
                    server_socket.sendto(packet.encode(), addr)
                except timeout:
                    continue
        except KeyboardInterrupt:
            print("\nServer: Shutting down...")
            exit()
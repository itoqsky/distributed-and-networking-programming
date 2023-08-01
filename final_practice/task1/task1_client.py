import argparse
import math
import os
import socket
import json

SERVER_IP = "0.0.0.0"
PORT = 50000

class Query:
    def __init__(self, type, key):
        self.type = type
        self.key = key

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.settimeout(5)
        queries = []
        queries.append(Query(type="A", key="example.com"))
        queries.append(Query(type="PTR", key="1.2.3.4"))
        queries.append(Query(type="CNAME", key="moodle.com"))
        try:
            for query in queries:
                try:
                    print(f"Client: Sending query for {query.key}")
                    packet = json.dumps({"type": query.type, "key": query.key})
                    client_socket.sendto(packet.encode(), (SERVER_IP, PORT))
                    data, addr = client_socket.recvfrom(1024)
                    response = json.loads(data)
                    print(f"Server: {response}")
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
                print("\nServer: Shutting down...")
                exit()

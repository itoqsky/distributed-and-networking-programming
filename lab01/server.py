import math
import os
from socket import socket, AF_INET, SOCK_DGRAM, timeout
import sys
import time
import re

MSS = 20480  # MSS = Server buffer size (20480) - data header size (4)
SERVER_IP = "0.0.0.0"

client_info = {
    "ip": None,
    "port": None,
    
    "file_name": None,
    "file_size": None,

    "seq": 0,
    "expecting_seq": 1,

    "chunk_num": 0,
    "chunk": b""
}

def start_conn(data, addr):
    client_info["ip"] = addr[0]
    client_info["port"] = addr[1]

    client_info["file_name"] = str(data[2])
    client_info["file_size"] = int(data[3])

    client_info["seq"] = int(data[1])
    client_info["expecting_seq"] = (int(data[1]) + 1) % 2

    client_info["chunk_num"] = 0
    client_info["chunk"] = b""

def clear_client_info():
    client_info["ip"] = None
    client_info["port"] = None

    client_info["file_name"] = ""
    client_info["file_size"] = 0

    client_info["seq"] = 0
    client_info["expecting_seq"] = 1

    client_info["chunk_num"] = 0
    client_info["chunk"] = b""

def send_ack(server_socket, clientAddr):
    server_socket.sendto(f"a|{str((int(client_info['seq']) + 1) % 2)}|".encode("iso-8859-1"), clientAddr)

if __name__ == "__main__":
    SERVER_PORT = int(sys.argv[1])

    with socket(AF_INET, SOCK_DGRAM) as server_socket:
        server_socket.bind((SERVER_IP, SERVER_PORT))
        server_socket.settimeout(5)
        print(f"('{SERVER_IP}', {SERVER_PORT}):\tListening...")
        try:
            while True:
                try:
                    msg, clientAddr = server_socket.recvfrom(MSS)
                    decData = msg.decode("iso-8859-1")
                    data = decData.split(decData[1])
                    if data[0] == "s":
                        start_conn(data, clientAddr)
                        if os.path.exists(client_info["file_name"]):
                            print(f"('{SERVER_IP}', {SERVER_PORT}):\tFile '{client_info['file_name']}' already exists, overwriting...")
                            with open(client_info["file_name"], 'w') as f:
                                f.truncate(0)
                        # print(client_info)
                        print(f"('{clientAddr[0]}', {clientAddr[1]}):\t{msg.decode('iso-8859-1')}")
                        send_ack(server_socket, clientAddr)
                    else:
                        if client_info["ip"] == clientAddr[0] and client_info["port"] == clientAddr[1]:
                            if int(data[1]) == client_info["expecting_seq"]:
                                client_info["seq"] = data[1]
                                client_info["expecting_seq"] = (int(data[1]) + 1) % 2
                                client_info["chunk"] = msg[4:]
                                client_info["chunk_num"] += 1
                                with open(client_info["file_name"], "ab") as f:
                                    f.write(client_info["chunk"])

                                print(f"('{clientAddr[0]}', {clientAddr[1]}):\t{data[0]}|{data[1]}|chunk{client_info['chunk_num']}")
                                send_ack(server_socket, clientAddr)

                    if os.path.exists(client_info["file_name"]) and client_info["file_size"] == os.path.getsize(client_info["file_name"]):
                        print(f"('{SERVER_IP}', {SERVER_PORT}):\tReceived {client_info['file_name']}")
                        clear_client_info()
                except timeout:
                    continue
        except KeyboardInterrupt:
            print("Shutting down...")
            # print(client_info)
            exit() 

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from _thread import start_new_thread
from threading import Lock
from PIL import Image
import random
from io import BytesIO

print_lock = Lock()
MSS =  1024
SERVER_IP = "127.0.0.1"
SERVER_PORT = 1234

def threaded(conn, addr):
    img = gen_pic()
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    img_bytes = buffer.getvalue()

    conn.sendall(img_bytes)

    print(f'Sent image to ({addr[0]}:{addr[1]})')

    print_lock.release()
    conn.close()


def gen_pic():
    img = Image.new('RGB', (10, 10))
    pixels = img.load()
    if pixels is not None:
        for i in range(10):
            for j in range(10):
                r = random.randint(0, 255)
                g = random.randint(0, 255)
                b = random.randint(0, 255)
                pixels[i, j] = (r, g, b)
    else:
        print("Error: pixels object is None")
    return img

        
def Main():
    with socket(AF_INET, SOCK_STREAM) as server_socket:
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        server_socket.bind((SERVER_IP, SERVER_PORT))
        server_socket.listen(5)
        print(f"Listening on {SERVER_IP}:{SERVER_PORT}")
        # server_socket.settimeout(5)
        try:
            while True:
                # try:
                conn, addr = server_socket.accept()
                print_lock.acquire()
                start_new_thread(threaded, (conn, addr))
                # except socket.timeout:
                #     print("Server: Timeout")           
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
            exit() 
            

if __name__ == "__main__":
    Main()

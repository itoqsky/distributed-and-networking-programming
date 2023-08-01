import os
import socket
import time
from threading import Lock
import multiprocessing

from PIL import Image

SERVER_URL = '127.0.0.1:1234'
FILE_NAME = 'IkramKamat.gif'
CLIENT_BUFFER = 1024
FRAME_COUNT = 5000

print_lock = Lock()

import concurrent.futures

def download_frames():
    global counter
    counter = 0
    t0 = time.time()

    if not os.path.exists('frames'):
        os.mkdir('frames')

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for i in range(FRAME_COUNT):
            executor.submit(threaded, i)

    return time.time() - t0

def threaded(i):
    ip, port = SERVER_URL.split(':')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, int(port)))
        image = b''
        while True:
            packet = s.recv(CLIENT_BUFFER)
            if not packet:
                break
            image += packet
        
        with open(f'frames/{i}.png', 'wb') as f:
            f.write(image)
    
    global counter
    counter += 1


def create_gif_worker(frame_id):
    return Image.open(f"frames/{frame_id}.png").convert("RGBA")

def create_gif():
    t0 = time.time()

    frames = []
    with multiprocessing.Pool(processes=os.cpu_count()) as pool:
        frames = pool.map(create_gif_worker, range(FRAME_COUNT))

    frames[0].save(FILE_NAME, format="GIF",
                   append_images=frames[1:], save_all=True, duration=500, loop=0)
    
    return time.time() - t0


if __name__ == '__main__':
    print(f"Frames download time: {download_frames()}")
    print(f"GIF creation time: {create_gif()}")

import requests
import numpy as np
import cv2
import streamlink
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

def initialize_video(video_url):
    video_capture = cv2.VideoCapture(video_url)
    if not video_capture.isOpened():
        print("Error opening video file.")
        return
    return video_capture

def calculate_initial_value(video_capture):
    ret, frame = video_capture.read()
    if not ret:
        return None, None
    W = frame.shape[1]
    H = frame.shape[0]
    color_i = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            yc_xc__pixel = frame[H // 2 + j, W // 2 + i]
            R_c, G_c, B_c = yc_xc__pixel[2], yc_xc__pixel[1], yc_xc__pixel[0]
            initial_value = (R_c << 16) + (G_c << 8) + B_c
            color_i += initial_value 
    color_i = color_i // 9
    x = (color_i) % (W//2) + W // 4
    y = (color_i) % (H//2) + H // 4
    return x, y

def set_thresholds(video_capture):
    frame_count = 0
    vt = 0
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    print(fps)
    while True:
        ret, frame = video_capture.read()
        if not ret:
            return None, None
        if frame_count == 3 * int(fps):
            vt = np.var(frame) // 2
            print(vt)
            break
        frame_count += 1
    th = 100
    return vt, th

def stream_audio(url, K):
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print(f"Błąd podczas próby dostępu do strumienia audio: {r.status_code}")
    for block in r.iter_content(K):
        audio_data = np.frombuffer(block, dtype=np.int8)
        if audio_data.size != 500:
            continue
        yield audio_data

def capture_video_frames(video_capture):
    while True:
        ret, frame = video_capture.read()
        if not ret:
            print('Coś się wykrzaczyło z wizją')
            break

        yield frame

def process_rgb_values(frame, x, y):
    if frame is not None:
        pixel = frame[y, x]
        R, G, B = pixel[2], pixel[1], pixel[0]
        return R, G, B
    return 0, 0, 0  # Default values if frame is None        

def generate_random_bits(audio_url, video_capture, n):
    R, G, B, R1, G1, B1, R2, G2, B2 = 0, 0, 0, 0, 0, 0, 0, 0, 0
    x, y = calculate_initial_value(video_capture)
    vt, th = set_thresholds(video_capture)
    runcnt = 0
    counter_bits = 0
    K = 500
    video_frames = capture_video_frames(video_capture)
    audio_stream = stream_audio(audio_url, K)
    bytes_list = []
    generated_bytes = 0

    while generated_bytes < n:
        audio_data, video_data = next(audio_stream), next(video_frames)
        W = video_data.shape[1]
        H = video_data.shape[0]
        i = 0
        random_bits = []
        watchdog = 0

        while i < 8:
            watchdog = 0
            while watchdog <= th:
                R, G, B = process_rgb_values(video_data, x, y)
                if np.square(np.int32(R) - np.int32(R1)) + np.square(np.int32(G) - np.int32(G1)) + np.square(np.int32(B) - np.int32(B1)) < vt:
                    x = (x + (R ^ G) + 1) % W
                    y = (y + (G ^ B) + 1) % H
                    watchdog += 1
                else:
                    break    

            if watchdog > th:
                break

            SN1 = audio_data[10 + (R * i + (G << 2) + B + runcnt) % (K // 2)]
            SN2 = audio_data[15 + (R * i + (G << 3) + B + runcnt) % (K // 2)]
            SN3 = audio_data[20 + (R * i + (G << 4) + B + runcnt) % (K // 2)]
            SN4 = audio_data[5  + (R * i + (G << 1) + B + runcnt) % (K // 2)]
            SN5 = audio_data[25 + (R * i + (G << 5) + B + runcnt) % (K // 2)]
            
            bit = R ^ G ^ B ^ R1 ^ G1 ^ B1 ^ R2 ^ G2 ^ B2 ^ SN1 ^ SN2 ^ SN3 ^ SN4 ^ SN5
            random_bits.append(bit & 1)
            i += 1
            counter_bits += 1
            if (counter_bits % 1000 == 0):
                print(counter_bits)
            if (counter_bits % 100000 == 0):
                runcnt += 1

            R1, G1, B1 = R, G, B
            x = (((R ^ x) << 4) ^ (G ^ y)) % W
            y = (((G ^ x) << 4) ^ (B ^ y)) % H

        if watchdog > th:
            print('Watchdog alert!!!')   
            continue
        R2, G2, B2 = R, G, B
        byte = 0
        for j in range(8):
            byte |= random_bits[j] << (7 - j)
        bytes_list.append(byte)
        generated_bytes += 1

    return bytes_list

# Przykładowe URL
streams = streamlink.streams("https://www.youtube.com/watch?v=QTTTY_ra2Tg")
# streams = streamlink.streams("https://www.youtube.com/watch?v=Gv3GRTgZ-oI")
stream_url = streams['best'].url  
audio_url = 'https://rs6-krk2.rmfstream.pl/rmf_fm'

video_capture = initialize_video(stream_url)

def my_get_random_bytes(n):
    return bytes(generate_random_bits(audio_url, video_capture, n))

def generate_rsa_key_pair(trng_function, key_size=1024):
    global get_random_bytes
    get_random_bytes = trng_function

    private_key = RSA.generate(key_size, randfunc=get_random_bytes)
    # private_key = RSA.generate(key_size)
    return private_key

def serialize_key(private_key, public_key):
    private_key_bytes = private_key.export_key(format='PEM')
    public_key_bytes = public_key.export_key(format='PEM')
    return private_key_bytes, public_key_bytes


private_key = generate_rsa_key_pair(my_get_random_bytes)
public_key = private_key.publickey()

private_key_bytes, public_key_bytes = serialize_key(private_key, public_key)


pwd = b'secret'

with open("myprivatekey.pem", "wb") as f:
    data = private_key.export_key(passphrase=pwd,
                                pkcs=8,
                                protection='PBKDF2WithHMAC-SHA512AndAES256-CBC',
                                prot_params={'iteration_count':131072})

    f.write(data)

with open("mypublickey.pem", "wb") as f:
    data = public_key.export_key()
    f.write(data)

# with open('private_key.pem', 'wb') as f:
#     f.write(private_key_bytes)

# with open('public_key.pem', 'wb') as f:
#     f.write(public_key_bytes)


video_capture.release()
cv2.destroyAllWindows()






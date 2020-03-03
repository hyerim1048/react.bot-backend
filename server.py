from aiohttp import web 
import socketio 
import io
import scipy.io.wavfile as wavf
import numpy as np
from preprocess.MFCC_generator import MFCC_generator
import webrtcvad 
import struct

# Async Socket IO Server 
sio = socketio.AsyncServer() 
# Aio Webapp 
app = web.Application() 
# bind socket io to webapp 
sio.attach(app)

async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')
    
TMP_DIR = '/wav_files'
vad = webrtcvad.Vad()
vad.set_mode(1)
sample_rate = 16000
frame_duration = 10 
length_per_frame = int(sample_rate * frame_duration / 1000)
@sio.on('mic')
async def print_message(sid, *data):

    print("Socket ID: ", sid)
    print(len(data), type(data))

    fs = 16000
    filename = f"{TMP_DIR}/{sid}.wav"
    vad_filename = f"{TMP_DIR}/{sid}_vad.wav"
    try: 
        prev_wav = wavf.read(filename, mmap=False)
        prev_data = list(prev_wav[1])
        print(type(prev_data),len(prev_data))
        prev_data.extend(list(data))
        print(len(prev_data))
        wavf.write(filename, fs, np.array(prev_data, dtype=np.int16))


        # vad test
        total_length = len(data)
        frame_num_per_data = total_length/length_per_frame  
        print(frame_num_per_data)
        vad_prev_wav = wavf.read(vad_filename, mmap=False)
        vad_prev_data = list(vad_prev_wav[1])
        vad_data = []
        for idx in range(int(frame_num_per_data)):
            frame = data[length_per_frame*idx:length_per_frame*(idx+1)]
            print(frame)
            if vad.is_speech(b"".join(struct.pack('<h',d) for d in frame), sample_rate):
                vad_data.extend(frame)
        print("vad: ", len(vad_data))
        vad_prev_data.extend(list(vad_data))
        wavf.write(vad_filename, fs, np.array(vad_prev_data, dtype=np.int16))

        #vad_data = [data[idx] for idx in range(int(frame_num_per_data))\
        #    if vad.is_speech(data[length_per_frame*(idx-1):length_per_frame*idx], sample_rate)]
        

        # mfcc test
        generator = MFCC_generator()
        arr = generator.get_wav_mfcc(filename, start=0, duration=10)
        np.save("/wav_files/sample_mfcc.npy", arr)
        await sio.emit('mic', "completed")
  
    except OSError as e: 
        wavf.write(filename, fs, np.array(data, dtype=np.int16))
        wavf.write(vad_filename, fs, np.array(data, dtype=np.int16))


# router
app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app)

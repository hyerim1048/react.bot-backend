from aiohttp import web 
import socketio 
import io
import scipy.io.wavfile as wavf
import numpy as np
from preprocess.MFCC_generator import MFCC_generator

# Async Socket IO Server 
sio = socketio.AsyncServer() 
# Aio Webapp 
app = web.Application() 
# bind socket io to webapp 
sio.attach(app)

async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')
    
global_data = []
TMP_DIR = '/wav_files'
@sio.on('mic')
async def print_message(sid, *data):

    print("Socket ID: ", sid)
    print(len(data), type(data))

    fs = 44100
    filename = f"{TMP_DIR}/{sid}.wav"
    try: 
        prev_wav = wavf.read(filename, mmap=False)
        prev_data = list(prev_wav[1])
        print(type(prev_data),len(prev_data))
        prev_data.extend(list(data))
        print(len(prev_data))
        wavf.write(filename, fs, np.array(prev_data, dtype=np.int16))

        generator = MFCC_generator()
        arr = generator.get_wav_mfcc(filename, start=0, duration=10)
        np.save("/wav_files/sample_mfcc.npy", arr)
        await sio.emit('mic', "completed")
  
    except OSError as e: 
        wavf.write(filename, fs, np.array(data, dtype=np.int16))


# router
app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app)

from aiohttp import web 
import socketio 
import io
import scipy.io.wavfile as wavf
import numpy as np
from preprocess.MFCC_generator import MFCC_generator
import webrtcvad 
import struct
import speech_recognition as speech_recog

# Async Socket IO Server 
sio = socketio.AsyncServer() 
# Aio Webapp 
app = web.Application() 
# bind socket io to webapp 
sio.attach(app)

async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')
    
# global
TMP_DIR = '/wav_files'
vad = webrtcvad.Vad()
vad.set_mode(1)
sample_rate = 16000
frame_duration = 10 # ms
length_per_frame = int(sample_rate * frame_duration / 1000)
one_second = int(1000/frame_duration)
redis = {}

@sio.on('mic')
async def print_message(sid, *data):

    print("Socket ID: ", sid)
    print(len(data), type(data))

    filename = f"{TMP_DIR}/{sid}.wav"
    vad_filename = f"{TMP_DIR}/{sid}_vad.wav"
    try: 
        prev_wav = wavf.read(filename, mmap=False)
        prev_data = list(prev_wav[1])
        print(type(prev_data),len(prev_data))
        prev_data.extend(list(data))
        print(len(prev_data))
        wavf.write(filename, sample_rate, np.array(prev_data, dtype=np.int16))


        # vad test
        total_length = len(data)
        frame_num_per_data = total_length/length_per_frame  
        vad_prev_wav = wavf.read(vad_filename, mmap=False)
        vad_prev_data = list(vad_prev_wav[1])
        vad_data = []
        for idx in range(int(frame_num_per_data)):
            frame = data[length_per_frame*idx:length_per_frame*(idx+1)]
            if vad.is_speech(b"".join(struct.pack('<h',d) for d in frame), sample_rate):
                redis['nonspeech_num'] = redis['nonspeech_num'] + 1
                vad_data.extend(frame)
        vad_prev_data.extend(list(vad_data))
        wavf.write(vad_filename, sample_rate, np.array(vad_prev_data, dtype=np.int16))

        if redis['nonspeech_num'] > one_second:
            redis['nonspeech_num'] = 0
            recog = speech_recog.Recognizer()
            with speech_recog.AudioFile(vad_filename) as audio_file:
                print("here ********************")
                audio_content = recog.record(audio_file)
                print(recog.recognize_google(audio_content))
            await sio.emit('fromSerer', "Happy")
        #vad_data = [data[idx] for idx in range(int(frame_num_per_data))\
        #    if vad.is_speech(data[length_per_frame*(idx-1):length_per_frame*idx], sample_rate)]
        

        # mfcc test
        generator = MFCC_generator()
        arr = generator.get_wav_mfcc(filename, start=0, duration=10)
        np.save("/wav_files/sample_mfcc.npy", arr)
        
  
    except OSError as e: 
        redis['nonspeech_num'] = 0
        wavf.write(filename, sample_rate, np.array(data, dtype=np.int16))
        wavf.write(vad_filename, sample_rate, np.array(data, dtype=np.int16))


# router
app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app)

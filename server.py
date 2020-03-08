from aiohttp import web 
import socketio 
import io
import scipy.io.wavfile as wavf
import numpy as np
from preprocess.MFCC_generator import MFCC_generator
import webrtcvad 
import struct
import speech_recognition as speech_recog

sio = socketio.AsyncServer() 
app = web.Application() 
# bind socket io to webapp 
sio.attach(app)


# global
TMP_DIR = '/wav_files'
redis = {}
vad = webrtcvad.Vad()
vad.set_mode(1)
sample_rate = 16000
frame_duration = 10 # ms
length_per_frame = int(sample_rate * frame_duration / 1000)
one_second = int(1000/frame_duration)

async def inference(request):
    vad_data = request.data # fix 
    tmp_wav_filename = "test.wav"
    wavf.write(tmp_wav_filename, sample_rate, np.array(vad_data, dtype=np.int16))
    # mfcc 
    generator = MFCC_generator()
    arr = generator.get_wav_mfcc(tmp_wav_filename, start=0, duration=10)
    np.save("/wav_files/sample_mfcc.npy", arr)
 

def append_and_save_wav_data(filename, data):
    prev_wav = wavf.read(filename, mmap=False)
    prev_data = list(prev_wav[1])
    prev_data.extend(list(data))
    wavf.write(filename, sample_rate, np.array(prev_data, dtype=np.int16))

def run_vad(frame_num_per_data, data):
    for idx in range(int(frame_num_per_data)):
        frame = data[length_per_frame*idx:length_per_frame*(idx+1)]
        if vad.is_speech(b"".join(struct.pack('<h',d) for d in frame), sample_rate):
            redis['nonspeech_num'] = redis['nonspeech_num'] + 1
            redis['vad_result'].extend(frame)


@sio.on('mic')
async def print_message(sid, *data):

    print("Socket ID: ", sid)
    print(len(data), type(data))

    filename = f"{TMP_DIR}/{sid}.wav"
    try: 
        append_and_save_wav_data(filename, data)
        total_length = len(data) # 1600
        frame_num_per_data = total_length/length_per_frame # 10 
        run_vad(frame_num_per_data, data)

        if redis['nonspeech_num'] > one_second:
            # request speech inference and await  
            result = {"result":"happy"}
            # request text inference and await 
            recog = speech_recog.Recognizer()
            try:
                with speech_recog.AudioFile(filename) as audio_file:
                    audio_content = recog.record(audio_file)
                    text_from_audio = recog.recognize_google(audio_content)
                
            except: 
                print("error")

            await sio.emit('fromSerer', result)
            redis['nonspeech_num'] = 0
            redis['vad_result'] = []

    except OSError as e: 
        redis['vad_result'] = []
        redis['nonspeech_num'] = 0
        wavf.write(filename, sample_rate, np.array(data, dtype=np.int16))

# router
app.router.add_get('/inference', inference)

if __name__ == '__main__':
    web.run_app(app)

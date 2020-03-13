import aiohttp
from aiohttp import web 
import socketio 
import io
import scipy.io.wavfile as wavf
import numpy as np
import webrtcvad 
import struct
import speech_recognition as speech_recog
import requests
import json
import time 

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
one_second = 10#int(1000/frame_duration/2)

# speech 
recog = speech_recog.Recognizer()

def append_and_save_wav_data(filename, data):
    prev_wav = wavf.read(filename, mmap=False)
    prev_data = list(prev_wav[1])
    prev_data.extend(list(data))
    wavf.write(filename, sample_rate, np.array(prev_data, dtype=np.int16))

def run_vad(frame_num_per_data, data):
    for idx in range(int(frame_num_per_data)):
        frame = data[length_per_frame*idx:length_per_frame*(idx+1)]
        if vad.is_speech(b"".join(struct.pack('<h',d) for d in frame), sample_rate):
            redis['vad_result'].extend(frame)
            if redis['nonspeech_num'] != 0:
                redis['nonspeech_num'] = 0
        else:
            redis['nonspeech_num'] = redis['nonspeech_num'] + 1

def speech_recognition(audio):
    filename = "test.wav"
    wavf.write(filename, sample_rate, np.array(audio, dtype=np.int16))
    try:
        with speech_recog.AudioFile(filename) as audio_file:
            audio_content = recog.record(audio_file)
            #print(len(audio_content), type(audio_content))
            with open ('./speech_key.json', 'r') as f:
                credential = f.read()
                context = recog.recognize_google_cloud(audio_content, language = "en-us", credentials_json = credential)
                print ("Google Speech Recognition thinks you said" + context)
            #text_from_audio = recog.recognize_google_cloud(audio_content, GOOGLE_CLOUD_SPEECH_CREDENTIALS)
            #print(text_from_audio)
            return context

    except speech_recog.UnknownValueError:
        print("Google Cloud Speech could not understand audio")
        redis['nonspeech_num'] = 0
        return None
    except speech_recog.RequestError as e:
        print("Could not request results from Google Cloud Speech service; {0}".format(e))
                    
async def hello(request):
        return web.Response(text="Hello, world")

@sio.on('mic')
async def print_message(sid, *data):

    filename = f"{TMP_DIR}/{sid}.wav"
    try: 
        append_and_save_wav_data(filename, data)
        total_length = len(data) # 1600
        frame_num_per_data = total_length/length_per_frame # 10 
        run_vad(frame_num_per_data, data)
        if len(redis['vad_result']) == 0:
            redis['nonspeech_num'] = 0
        print(len(redis['vad_result']),redis['nonspeech_num'],one_second)
        if redis['nonspeech_num'] > one_second:
            print("여기까진 왔다", len(redis['vad_result']))
            t1 = time.time()
            recog_data = "pass!" # speech_recognition(redis['vad_result'])
            dt = time.time() - t1
            print("Google Cloud Execution time: %0.02f seconds" % (dt))
            t1 = time.time()
            if recog_data:
                headers = {'Content-Type': 'application/json', 'Accept':'application/json'}
                result = requests.post("http://35.221.251.166:8000/predict",\
                    data=json.dumps({'data':list(redis['vad_result'])}), headers=headers)
                dt = time.time() - t1
                print("Sentiment Analysis time: %0.02f seconds" % (dt))
                if result:
                    print(result.text)
                    redis['nonspeech_num'] = 0
                    await sio.emit('fromSerer', result.text)

    # #app.logger.info
     
    

    except OSError as e: 
        print(e)
        redis['vad_result'] = []
        redis['nonspeech_num'] = 0
        wavf.write(filename, sample_rate, np.array(data, dtype=np.int16))

app.add_routes([web.get('/', hello)])

if __name__ == '__main__':
    web.run_app(app)

"""
            # request text inference and await 
            recog = speech_recog.Recognizer()
            try:
                with speech_recog.AudioFile(filename) as audio_file:
                    audio_content = recog.record(audio_file)
                    text_from_audio = recog.recognize_google_cloud(audio_content,"./speech_key.json")
                     except: 
                print("error")
"""

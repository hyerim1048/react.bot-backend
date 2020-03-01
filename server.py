from aiohttp import web 
import socketio 
import io
import scipy.io.wavfile as wavf
import numpy as np

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

@sio.on('mic')
async def print_message(sid, *data):
    # a new event of type message through socket.io
    # socket ID and the message 
    print("Socket ID: ", sid)
    print(len(data), type(data))

    fs = 44100
    out_f = '/wav_files/out.wav'
    global_data.extend(list(data))
    print(len(global_data))
    wavf.write(out_f, fs, np.array(global_data, dtype=np.int16))
    await sio.emit('mic', "completed")

  
# router
app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app)

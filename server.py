from aiohttp import web 
import socketio 

# Async Socket IO Server 
sio = socketio.AsyncServer() 
# Aio Webapp 
app = web.Application() 
# bind socket io to webapp 
sio.attach(app)

async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')
    
    mic 
    
    
@sio.on('message')
async def print_message(sid, message):
    # a new event of type message through socket.io
    # socket ID and the message 
    print("Socket ID: ", sid)
    print(message)
    
    await sio.emit('message', message[::-1])

  
# router
app.router.add_get('/', index)

if __name__ == '__main__':
    web.run_app(app)
import os
import time
import http.server
import socket
import threading

import pychromecast
from gtts import gTTS

ghome_ip = '192.168.1.1'
PORT = 8000

say = '''
ui
'''

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.connect(('8.8.8.8', 80))
    local_ip, _ = s.getsockname()


class StoppableHTTPServer(http.server.HTTPServer):
    def run(self):
        try:
            print('Server started at %s:%s!' % (local_ip, self.server_address[1]))
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()

server = StoppableHTTPServer(('', PORT), http.server.SimpleHTTPRequestHandler)
thread = threading.Thread(None, server.run)
thread.start()

ghome = pychromecast.Chromecast(ghome_ip)
print(ghome)
ghome.wait()

volume = ghome.status.volume_level
ghome.set_volume(0)

os.makedirs('cache', exist_ok=True)
fname = 'cache/cache.mp3'

tts = gTTS(say,lang='pt')
tts.save(fname)

# ready to serve the mp3 file from server
mc = ghome.media_controller

mp3_path = 'http://%s:%s/%s' % (local_ip, PORT, fname)
mc.play_media(mp3_path, 'audio/mp3')
# mc.play_media('http://www.hochmuth.com/mp3/Tchaikovsky_Nocturne__orch.mp3', 'audio/mp3')

# pause atm
mc.block_until_active()
mc.pause()

# volume up
time.sleep(0.5)
ghome.set_volume(volume)
time.sleep(1)

# play
mc.play()
while not mc.status.player_is_idle:
    time.sleep(1)

# kill all
mc.stop()
ghome.quit_app()
server.shutdown()
os.remove(fname)
thread.join()
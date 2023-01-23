import os
import time
import http.server
import socket
import threading
import pychromecast
import json

from flask import Flask, jsonify, request
from gtts import gTTS

with open('config.json', 'r') as fcc_file:
  fcc_data = json.load(fcc_file)
  config_ip = str(fcc_data['ip'])
  config_lang = str(fcc_data['defaultLanguage'])
  webServerPort = int(fcc_data['WebServerPort'])
  PORT = int(fcc_data['serverPort'])

app= Flask(__name__)
@app.route("/message", methods=["POST"])

def setName():
    if request.method=='POST':
        # -=-=-
        posted_data = request.get_json()
        data = posted_data['message']
        
        if posted_data['lang']:
          set_lang = posted_data['lang']
          
        say = data
        
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

        ghome = pychromecast.Chromecast(config_ip)
        print(ghome)
        ghome.wait()

        volume = ghome.status.volume_level
        ghome.set_volume(0)

        os.makedirs('cache', exist_ok=True)
        fname = 'cache/cache.mp3'

        tts = gTTS(say,lang=set_lang)
        tts.save(fname)

        # ready to serve the mp3 file from server
        mc = ghome.media_controller

        mp3_path = 'http://%s:%s/%s' % (local_ip, PORT, fname)
        mc.play_media(mp3_path, 'audio/mp3')
      
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
        
        return jsonify(str(str("Google Nest said: " + data)))
        # -=-=-
      
if __name__=='__main__':
    app.run(debug=True, host="0.0.0.0", port=webServerPort)
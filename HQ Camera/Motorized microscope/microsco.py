# Motorized microscope with Raspberry Pi HQ camera and HTML interface
# Source code based on the Web streaming example from the official PiCamera package
# http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming
# Tutorial https://diyprojects.io/motorized-microscope-hq-camera-raspberry-pi-python-html-interface/
# Tutoriel https://projetsdiy.fr/microscope-motorise-camera-hq-raspberrypi-interface-html/


import io, picamera, logging, socketserver, os
from statistics import mean 
from threading import Condition, Thread
from http import server
import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib
import board, time, neopixel

#define GPIO pins
GPIO_pins = (14, 15, 18)    # Microstep Resolution MS1-MS3 -> GPIO Pin
direction= 20               # Direction Pin 
step = 21                   # Step Pin
step_per_mm = 72            # Step by millimeter | stepper per millimeter
distance = 72               # By default move 1mm => 72 steps per mm
stepper = "1mm"
debug    = False

# LED strip configuration
LED_COUNT   = 16            # Number of LED ring      | Nombre de LED de l'anneau Neopixel
LED_PIN     = board.D12     # GPIO pin. Don't use D10 | Ne fonctionne pas sur la broche D10
LED_BRIGHTNESS = 1          # LED brightness, from 0 to 1 | Niveau de luminosité, compris entre 0 à 1
LED_ORDER = neopixel.GRB    # Order of LED colours. May also be RGB, GRBW, or RGBW | Type de LED
ring_status = False         # LED Ring status
ring_status_label = "Off"   # LED Ring status for user | Etat de l'anneau de LED affiché sur la page Web
color = "white"             # Default color | Couleur d'éclairage par défaut (blanc)

camera_rotation = 270       # Image rotation in degrees (0,90,180,270) | rotation de l'image en degrées (0,90,180,270)

# Create instance for the Stepper Motor
mymotortest = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")
print("A4988 initialized")

# Neopixel Ring object
# auto_write must be set to False to change color | l'option auto_write doit être False pour pouvoir changer de couleur 
ring = neopixel.NeoPixel(board.D12, LED_COUNT, brightness = LED_BRIGHTNESS, auto_write=False, pixel_order = LED_ORDER)
ring.fill((0,0,0))
ring.show()

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def getPage(self):
        PAGE="""
            <html>
                <head>
                    <meta charset="utf-8">
                    <!-- <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=yes"> -->

                    <!-- Bootstrap CSS -->
                    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">

                    <title>Raspberry Pi HQ Camera Magnifying</title>
                </head>
                <body>
                <div class="container">
                    <div class="row">
                    <div class="col-sm-9" style="padding:10">
                        <img src="stream.mjpg" style="width:100%">
                        <p>How to <a href="https://projetsdiy.fr">in english</a> | Comment faire <a href="https://projetsdiy.fr/microscope-motorise-camera-hq-raspberrypi-interface-html/">en français</a></p>
                    </div>
                    <div class="col-sm-3" style="padding:10">
                        <div class="row">
                            <div class="col-4">
                                <form method="POST" action="up">
                                    <button type="submit" class="btn btn-primary">Up</button>
                                </form>
                        
                            </div> 
                            <div class="col-4">
                                <form method="POST" action="down" class="center-block">
                                    <button type="submit" class="btn btn-primary">Down</button>
                                </form>
                            </div>   
                        </div>
                        <div></div>
                        <div class="row">
                            <div class="col-3">
                                <form method="POST" action="switchonoffring">
                                    <button name="ringcolor" value="light" type="submit" style="font-size=40" class="btn btn-primary" >{button_label}</button>
                                </form>
                            </div>
                            <div class="col-2">    
                                <form method="POST" action="changecolor">
                                    <button name="ringcolor" value="light" type="submit" style="font-size=40" class="btn btn-light" > W </button>
                                </form>
                            </div>
                            <div class="col-2">     
                                <form method="POST" action="changecolor" >
                                    <button name="ringcolor" value="red" type="submit" class="btn btn-danger"> R </button>
                                </form>
                            </div>
                            <div class="col-2">     
                                <form method="POST" action="changecolor" >
                                    <button name="ringcolor" value="yellow" type="submit" class="btn btn-warning"> Y </button>
                                </form>
                            </div>
                            <div class="col-2">     
                                <form method="POST" action="changecolor" >
                                    <button name="ringcolor" value="green" type="submit" class="btn btn-success"> G </button>
                                </form>
                            </div>    
                        </div>
                        <form method="POST" action="setdistance">
                            <div class="btn-group" role="group" aria-label="Basic example" >
                            <button name="distance" type="submit" class="btn btn-secondary" value="7">0.1 mm</button>
                            <button name="distance" type="submit" class="btn btn-secondary" value="73">1 mm</button>
                            <button name="distance" type="submit" class="btn btn-secondary" value="727">10 mm</button>
                            </div>
                        </form>
                        <h3>Info</h3>
                        <p>Step: {step}</p>
                        <p>LED: {ring_status}</p>
                        <p>Color: {ring_color}</p>
                    </div>
                    </div>  
                </body>
            </html>
            """.format(ring_status=ring_status_label, ring_color=color,button_label= "OFF" if ring_status else "ON", step=stepper)
        return PAGE

    def changeLedColor(self):
        global ring_status, color
        if ring_status == True:
          print("color changed to ", color)  
          if color == "red":
            print('red')
            ring.fill((255,0,0))
            ring.show()
          elif color == "yellow":
            print('yellow')
            ring.fill((255,255,0))
            ring.show()
          elif color == "green":
            print('green')
            ring.fill((70,245,10))
            ring.show()
          else:
            print('white')
            ring.fill((255,255,255))
            ring.show()
        else:
           print("Ring if OFF")

    def do_POST(self):
        global distance, ring_status, color, stepper, ring_status_label, step_per_mm, distance
        content_length = int(self.headers['Content-Length']) 
        post_data = self.rfile.read(content_length) 
        if self.path == '/up':
            print("Go Up to ", distance)
            mymotortest.motor_go(False, "Full" , distance, 0.001 , False, .05)
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/down':
            print("Go Down to ", distance)
            mymotortest.motor_go(True, "Full" , distance, 0.001 , False, .05)
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == "/changecolor":
            color = post_data[10:].decode('utf-8')
            self.changeLedColor()
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == "/switchonoffring":          
            try:
                if ring_status == False:
                  ring_status = True
                  ring_status_label = "On"
                  self.changeLedColor()
                  print("Switch ON LED")
                else:
                  ring.fill((0, 0, 0))
                  ring.show()
                  ring_status_label = 'Off'
                  ring_status = False
                  print("Switch OFF LED")
            except Exception as e:
                logging.warning('Neopixel error: %s', str(e))
            
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()   
        elif self.path == '/setdistance':
            distance = int(post_data[9:])
            stepper = str( round(distance / step_per_mm, 1) ) + "mm"
            print("Set stepper to ", distance)
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers() 
        else:
            self.send_error(404)
            self.end_headers()   
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = self.getPage().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='1296x972', framerate=24) as camera:
    
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    camera.rotation = camera_rotation
    camera.start_recording(output, format='mjpeg')
    try:
        #print("try to get distance")

        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)

        server.serve_forever()
        
    #finally:
    #    print("Stop camera stream")
    #    camera.stop_recording()
    except KeyboardInterrupt:
        print("Shtdown HTTP server")
        server.shutdown()
        
        print("Close camera")
        camera.stop_recording()
        
        print("Switch off LED and cleanup GPIO")
        ring.fill((0,0,0))
        ring.show()
        time.sleep(0.1)
        ring.deinit()
        GPIO.cleanup()
        
        os._exit(0) 
        

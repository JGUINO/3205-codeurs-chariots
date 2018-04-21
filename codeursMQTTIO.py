#!/usr/bin/env python

################################################################################
# 
# encoderd.py is a python based daemon for persistant monitoring of the state of
#   any number of quadrature rotary encoders attached to a raspberry pi
# 
# Written by: 
#    Matthew Ebert 
#    Department of Physics
#    University of Wisconsin - Madison
#    mfe5003@gmail.com
# 
# Python Daemon bootstrap code by:
#    Sander Marechal
#    http://www.jejik.com/ 
#    http://web.archive.org/web/20160305151936/http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
#
# This daemon will poll the GPIO pins for each attached rotary encoder and
#   convert the count to an angle.
#   Settings are listed in encoder-settings.py file.
#
################################################################################

import os, sys, time
from daemon import Daemon
import logging
from codeurs_rotatifs import RotaryEncoder
import codeurs_rotatifs as rotary_encoder
#import gaugette.rotary_encoder as rotary_encoder
# JGUI


import gaugette.gpio
#import gaugette.platform
import paho.mqtt.client as mqtt
from maxi02IO import Maxi02IO

import encoderd_settings as settings
import os.path

class MyusbIO(Maxi02IO):
    def rien(self):
        sleep(0.0001)
        
usbIO = MyusbIO(sys.argv)
IOV=usbIO.io




def controle_angles(self, angAVD, angAVG, angAR, FangAR90):
    
    if angAR == 90 and FangAR90 == False :
        FangAR90 = True
        client.publish("capteurs/angle/AR", "90", qos=0, retain=False)
        usbIO.changeRelais(IOV,0)
    elif angAR != 90 :
        FangAR90 = False
        #usbIO.changeRelais(0)
    return FangAR90

def on_connect(client, userdata, flags, rc):
      userdata.logger.info("Connected with result code "+str(rc))
      
def on_message(client, userdata, msg):
      userdata.logger.info(msg.topic+" "+str(msg.payload))
  
def on_publish(client, obj , mid):
      obj.logger.info("publication reussie")

client=mqtt.Client()

class MyDaemon(Daemon):
  global Vcontrole_angles
  Vcontrole_angles = False
  def run(self):
    global Vcontrole_angles
    Vcontrole_angles = False
    self.setup()
    #angleAVG = Int()
    angleAVG = 0
    #angleAVD = Int()
    angleAVD = 0
    #angleAR = Int()
    angleAR = 0
    
    FangAR90 = False
    #JGUI TEST
    #usbIO.changeRelais(0)
    
    while True:
      for enc in self.encoders:
        steps = enc['obj'].get_cycles()
        # JGUI steps = enc['obj'].get_steps()
        if steps != 0:
          enc['angle'] += enc['calibration']*steps
          #JGUI
          #client.publish('capteurs/angle', payload=str(angle), qos=0, retain=False)
          self.saveAngle(enc) 
          self.logger.info("Encoder {}: {} movement detected. Angle is now {} degrees.".format(enc['number'],enc['name'],enc['angle']))
        if enc['number'] == 0:
           angleAVG=int(enc['angle'])
        elif enc['number'] == 1:
           angleAVD=int(enc['angle'])
        elif enc['number'] == 2:
           angleAR=int(enc['angle'])   
        if Vcontrole_angles == False :
            Vcontrole_angles = True
            FangAR90 = controle_angles (self, angleAVD, angleAVG, angleAR, FangAR90)
            Vcontrole_angles = False
     
      #time.sleep(settings.REFRESH_RATE)
      time.sleep(0.01)

  def setup(self):
    with open(os.path.join(settings.DIR,'testlog.log'),'w') as log:
      log.write("started\n")
    self.setupLogger()
    #JGUI
    self.setupConnect()
    self.setupEncoders()
    self.logger.info("setups encodeurs finis")
    
  #JGUI connection au broker
  def setupMaxiIO(self):
    return
        
  def setupConnect(self):
     client.reinitialise()
     client.user_data_set(self)
     client.on_connect = on_connect
     client.on_message = on_message
     client.on_publish = on_publish
     client.connect("localhost", 1883, 60)
     client.loop_start()
     client.publish("capteurs/angle", "Demarrage des capteurs", qos=0, retain=False)
         

  def setupLogger(self):
    pass
    # set up logger
    self.logger = logging.getLogger(__name__)
    self.logger.setLevel(logging.DEBUG)
    # create a file handler for the logger
    fh = logging.FileHandler(settings.LOG_FILE)
    fh.setLevel(logging.DEBUG)
    # format logging
    fformatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(fformatter)
    self.logger.addHandler(fh)

  def setupEncoders(self):
    self.encoders=[]
    enc_cnt = 0
    for enc in settings.ENCODERS:
      self.encoders.append(enc)
      # ligne JGUI
      gpio = gaugette.gpio.GPIO()
      pinA=enc['pinA']
      pinB=enc['pinB']
      # start a monitoring thread avec gpio par JGUI
      
      self.encoders[enc_cnt]['obj'] = rotary_encoder.RotaryEncoder.Worker(gpio,pinA,pinB)
      self.encoders[enc_cnt]['number'] = enc_cnt
      self.encoders[enc_cnt]['obj'].start()
      self.logger.info("Encoder {}: {} registered. Worker thread started.".format(enc_cnt,enc['name']))
      client.publish("capteurs/angle/"+str(enc['name'])+str(enc_cnt),"Demarrage encodeur", qos=0, retain=False)
      # read recorded angle if log file exists
      self.readAngle(enc)
      enc_cnt += 1

    self.encoder_count = enc_cnt
    self.logger.info("Registered encoders: {}".format(str(enc_cnt)))
      
  def readAngle(self, encoder):
    try: 
      with open(encoder['logfile'], 'r') as fi:
        encoder['angle'] = float(fi.readline())
    except:
      encoder['angle'] = 0.0
      self.saveAngle(encoder)
    msg = "Encoder: {}: {} angle set to {} degrees."
    self.logger.info(msg.format(encoder['number'],encoder['name'],encoder['angle']))
    return encoder['angle']

  def saveAngle(self, encoder):
    angle = encoder['angle']
    client.publish("capteurs/angle/"+str(encoder['name'])+str(encoder['number']), str(angle), qos=0, retain=False)
    self.logger.info("on publie")
    with open(encoder['logfile'], 'w') as fo:
      fo.write(str(angle))
    self.logger.debug("Encoder: {}: {} angle recorded as {} degrees.".format(encoder['number'],encoder['name'],angle))
    #JGUI
    #client.single("capteurs/angle", str(angle), qos=0, retain=False)

  def zero(self):
    for enc in self.encoders:
      enc['angle'] = 0.0
      saveAngle(enc)


if __name__ == "__main__":
  daemon = MyDaemon(settings.PID_FILE)
  #daemon = MyDaemon('/tmp/daemon-example.pid')
  if len(sys.argv) == 3:
    if 'start' == sys.argv[1]:
      daemon.start()
    if 'foreground' == sys.argv[1]:# for debugging
      daemon.run()
    elif 'stop' == sys.argv[1]:
      #client.disconnect()
      daemon.stop()
    elif 'restart' == sys.argv[1]:
      daemon.restart()
    elif 'zero' == sys.argv[1]:
      daemon.zero()
    else:
      print( "Unknown command")
      sys.exit(2)
    sys.exit(0)
  else:
    print ("usage: ",sys.argv[0], " start|stop|restart|foreground|zero NomduMaxiIOV2 ") 
    sys.exit(2)

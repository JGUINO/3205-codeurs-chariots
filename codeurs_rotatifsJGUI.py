#----------------------------------------------------------------------
# rotary_encoder.py from https://github.com/guyc/py-gaugette
# Guy Carpenter, Clearwater Software
#
# This is a class for reading quadrature rotary encoders
# like the PEC11 Series available from Adafruit:
#   http://www.adafruit.com/products/377
# The datasheet for this encoder is here:
#   http://www.adafruit.com/datasheets/pec11.pdf
#
# This library expects the common pin C to be connected
# to ground.  Pins A and B will have their pull-up resistor
# pulled high.
#

import math
import threading
import time
import RPi.GPIO as GPIO

class RotaryEncoder:

    def __init__(self, a_pin, b_pin):
        #self.gpio = gpio
        GPIO.setmode(GPIO.BCM)
        self.a_pin = a_pin
        self.b_pin = b_pin

        #self.gpio.setup(self.a_pin, self.gpio.IN, self.gpio.PUD_UP)
        GPIO.setup(a_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        #self.gpio.setup(self.b_pin, self.gpio.IN, self.gpio.PUD_UP)
        GPIO.setup(b_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.steps = 0
        self.last_delta = 0
        self.r_seq = self.rotation_sequence()

        # steps_per_cycle and self.remainder are only used in get_cycles which
        # returns a coarse-granularity step count.  By default
        # steps_per_cycle is 4 as there are 4 steps per
        # detent on my encoder, and get_cycles() will return a signed
        # count of full detent steps.
        self.steps_per_cycle = 4
        self.remainder = 0

    # Gets the 2-bit rotation state of the current position
    # This is deprecated - we now use rotation_sequence instead.
    def rotation_state(self):
        #a_state = self.gpio.input(self.a_pin)
        a_state = GPIO.input(self.a_pin)
        #b_state = self.gpio.input(self.b_pin)
        b_state = GPIO.input(self.b_pin)
        r_state = a_state | b_state << 1
        return r_state

    # Returns the quadrature encoder state converted into
    # a numerical sequence 0,1,2,3,0,1,2,3...
    #
    # Turning the encoder clockwise generates these
    # values for switches B and A:
    #  B A
    #  0 0
    #  0 1
    #  1 1
    #  1 0
    # We convert these to an ordinal sequence number by returning
    #   seq = (A ^ B) | B << 2
    #
    def rotation_sequence(self):
        #a_state = self.gpio.input(self.a_pin)
        a_state = GPIO.input(self.a_pin)
        #b_state = self.gpio.input(self.b_pin)
        b_state = GPIO.input(self.b_pin)
        r_seq = (a_state ^ b_state) | b_state << 1
        return r_seq

    def update(self):
        delta = 0
        r_seq = self.rotation_sequence()
        if r_seq != self.r_seq:
            delta = (r_seq - self.r_seq) % 4
            if delta == 3:
                delta = -1
            elif delta == 2:
                delta = int(math.copysign(delta, self.last_delta))  # same direction as previous, 2 steps

            self.last_delta = delta
            self.r_seq = r_seq
        self.steps += delta

    def get_steps(self):
        steps = self.steps
        self.steps = 0
        return steps

    # get_cycles returns a scaled down step count to match (for example)
    # the detents on an encoder switch.  If you have 4 delta steps between
    # each detent, and you want to count only full detent steps, use
    # get_cycles() instead of get_delta().  It returns -1, 0 or 1.  If
    # you have 2 steps per detent, set encoder.steps_per_cycle to 2
    # before you call this method.
    def get_cycles(self):
        # python negative integers do not behave like they do in C.
        #   -1 // 2 = -1 (not 0)
        #   -1 % 2 =  1 (not -1)
        # // is integer division operator.  Note the behaviour of the / operator
        # when used on integers changed between python 2 and 3.
        # See http://www.python.org/dev/peps/pep-0238/
        self.remainder += self.get_steps()
        #JGUI
        cycles = self.remainder // self.steps_per_cycle
        self.remainder %= self.steps_per_cycle # remainder always remains positive
        return cycles

#JGUI essayee mais non lancee en fait
    #def start(self):
    #    def isr():
    #        self.update()
    #    self.gpio.trigger(self.a_pin, self.gpio.EDGE_BOTH, isr)
    #    self.gpio.trigger(self.b_pin, self.gpio.EDGE_BOTH, isr)

    class Worker(threading.Thread):
        def isr(self, pin):
            self.encoder.update()
        
        def __init__(self, a_pin, b_pin):
            threading.Thread.__init__(self)
            self.lock = threading.Lock()
            self.stopping = False
            self.encoder = RotaryEncoder(a_pin, b_pin)
            self.daemon = True
            self.delta = 0
            self.delay = 1
            GPIO.add_event_detect(a_pin, GPIO.BOTH, callback=self.isr)
            GPIO.add_event_detect(b_pin, GPIO.BOTH, callback=self.isr)


        def run(self):
            return True
            #while not self.stopping:
            #    self.encoder.update()
            #    time.sleep(self.delay)
            # JGUI essai infructueux self.encoder.start()    

        def stop(self):
            self.stopping = True

        def get_steps(self):
            return self.encoder.get_steps()

        def get_cycles(self):
            return self.encoder.get_cycles()
        
        
   
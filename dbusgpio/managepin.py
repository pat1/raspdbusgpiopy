#!/usr/bin/python

import RPi.GPIO as GPIO

class pin(object):

  def __init__(self,channel,state=False,mode="pool",pull=None,frequency=None,dutycycle=0.,bouncetime=None,eventstatus=None,myfunction=None):
    """
    channel : pin to manage (1-23)
    state : True, False
    mode : in, out, poll, pwm
    pull : up, down, None
    frequency : freq Hz, None
    dutycycle : 0.-100.
    bouncetime : milliseconds, software debouncing 
    eventstatus : event to manage (1/0/None) if None both events will be take in account
    myfunction : function to call on events
    """
    self.channel=channel
    self.state=state
    self.mode=mode
    self.pull=pull
    self.frequency=frequency
    self.dutycycle=dutycycle
    self.bouncetime=bouncetime
    self.eventstatus=eventstatus
    self.myfunction=myfunction
    
    self.initialize()

  def initialize(self):

    if self.mode == "poll" or self.mode == "in":
      # set up GPIO output with pull-up control
      #   (pull_up_down be PUD_OFF, PUD_UP or PUD_DOWN, default PUD_OFF)
      if self.pull == "up":
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      elif self.pull == "down":
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
      else:
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    if self.mode == "out":
      GPIO.setup(self.channel, GPIO.OUT)
      GPIO.output(self.channel, self.state)
    
    elif self.mode == "pwm":

      GPIO.setup(self.channel, GPIO.OUT)
      self.pwm = GPIO.PWM(self.channel, self.frequency)
      self.pwm.start(self.dutycycle)

    elif self.mode == "poll":
      pass

    elif self.mode == "in":

      if self.bouncetime is None:
        GPIO.add_event_detect(self.channel, GPIO.BOTH, callback=self.manageevent)
      else:
        #manage contact bounce.
        #Contact bounce (also called chatter) is a common problem
        #with mechanical switches and relays. Switch and relay contacts are
        #usually made of springy metals. When the contacts strike together,
        #their momentum and elasticity act together to cause them to bounce
        #apart one or more times before making steady contact. The result
        #is a rapidly pulsed electric current instead of a clean transition
        #from zero to full current. The effect is usually unimportant in
        #power circuits, but causes problems in some analogue and logic
        #circuits that respond fast enough to misinterpret the on-off pulses as a data stream.

        GPIO.add_event_detect(self.channel, GPIO.BOTH, callback=self.manageevent,bouncetime=self.bouncetime)

  def getstatus(self):
    if self.mode=="pool" or self.mode == "in" or self.mode == "out":
      self.status=GPIO.input(self.channel)
    else:
      self.status=None
      
    return self.status


  def setstatus(self,state):
    if self.mode=="out":
      GPIO.output(self.channel, state)
      self.state=state
    else:
      self.status=None
      
    return self.status


  def changepwm(self,frequency=None,dutycycle=None):
    """
    change a running pwm
    """

    if frequency is None : frequency=self.frequency
    if dutycycle is None : dutycycle=self.dutycycle

    if self.mode == "pwm":

      if frequency != self.frequency:
        self.pwm.ChangeFrequency(frequency)
        self.frequency=frequency

      if dutycycle != self.dutycycle:
        self.pwm.ChangeDutyCycle(dutycycle)
        self.dutycycle=dutycycle

  def stoppwm(self):

    if self.mode == "pwm":
      self.pwm.stop()


  def removeevent(self):
    GPIO.remove_event_detect(self.channel)


  def delete(self):
  
    self.stoppwm()
    self.removeevent()

    self.mode="in"
    self.pull=None

    self.initialize()

    #GPIO.cleanup(channel=self.channel)

  def manageevent(self,channel):
    #print "My Event happen! ",channel
    if self.channel != channel:
      print "mmm... somethink is wrong ! channel is not coerent."
      return

    status=GPIO.input(channel )

    if self.myfunction is not None :
      if self.eventstatus is None:
        event=True
      elif self.eventstatus == status:
        event=false
      else:
        event=True
    else:
      event=false

    self.status=status
    if event:
      self.myfunction(self)

def main():
  import time

  def myfunction(pin):
    print "I get my new pin status : ",pin.channel,pin.status


  # to use Raspberry BCM pin numbers
  GPIO.setmode(GPIO.BCM)
  dutycycle=0.

  pin18=pin(channel=18,mode="in",pull="up",bouncetime=200,myfunction=myfunction)
  pin23=pin(channel=23,mode="pwm",frequency=50.,dutycycle=dutycycle)

  while True:
    try:
      print "I am sleeping ..."
      time.sleep(2)
      print "pin 18 status=",pin18.getstatus()
      #pin23.setstatus(not pin23.getstatus())
      dutycycle+=10.
      if dutycycle > 100. :
        dutycycle=0.
      pin23.changepwm(dutycycle=dutycycle)
      print "pin 23 dutycycle=",dutycycle,pin23.dutycycle

    except:
      raise
      print
      print "Exit"
      pin18.delete()
      break

    # to reset every channel that has been set up by this program to INPUT 
    # with no pullup/pulldown and no event detection.
  GPIO.cleanup()

if __name__ == '__main__':
  main()  # (this code was run as script)

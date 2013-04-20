#!/usr/bin/python

import RPi.GPIO as GPIO

class pin(object):


  def __init__(self,channel,state=False,mode="poll",pull=None,frequency=None,dutycycle=None,bouncetime=None,eventstatus=None,myfunction=None):

    """
    channel : pin to manage (1-23)
    state : True, False
    mode : in, out, poll, pwm
    pull : up, down, None
    frequency : freq Hz, None
    dutycycle : 0.-100., None
    bouncetime : milliseconds, software debouncing , None
    eventstatus : event to manage (1/0/None) if None both events will be take in account
    myfunction : function to call on events
    """
    self.channel=channel
    self._state=state
    self._mode=mode
    self._pull=pull
    self._frequency=frequency
    self._dutycycle=dutycycle
    self._bouncetime=bouncetime
    self.eventstatus=eventstatus
    self.rpi_revision=None
    self.version=None
    self.myfunction=myfunction
    
    self.initialize()


  @property
  def status(self):

    if self.mode=="poll" or self.mode == "in" or self.mode == "out":
      self._status=GPIO.input(self.channel)
    else:
      self._status=None
    return self._status

  @status.setter
  def status(self, value):

    if self.mode=="out":
      GPIO.output(self.channel, value)
      self._state=value
    else:
      self._status=None
      

  @property
  def mode(self):
    return self._mode

  @mode.setter
  def mode(self, value):

    if not value in ("in","out","poll"):
      print "mode can be: ",("in","out","poll")
    else:
      self.stoppwm()
      self.removeevent()
      self._mode=value
      self.initialize()


  @property
  def pull(self):
    return self._pull

  @pull.setter
  def pull(self, value):

    self._pull=value

#    if self.mode == "poll" or self.mode == "in":
#      # set up GPIO output with pull-up control
#      #   (pull_up_down be PUD_OFF, PUD_UP or PUD_DOWN, default PUD_OFF)
#      if self.pull == "up":
#        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#      elif self.pull == "down":
#        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#      else:
#        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

#oppure
    self.mode=self.mode


  @property
  def bouncetime(self):
    return self._bouncetime

  @bouncetime.setter
  def bouncetime(self, value):
    self._bouncetime=value


  @property
  def frequency(self):
    return self._frequency


  @frequency.setter
  def frequency(self, frequency):
    """
    change a running pwm
    """
    if frequency is None : frequency=self.frequency
    if self.mode == "pwm":

      if frequency != self.frequency:
        self.pwm.ChangeFrequency(frequency)
    self._frequency=frequency


  @property
  def dutycycle(self):
    return self._dutycycle

  @dutycycle.setter
  def dutycycle(self, dutycycle):
    """
    change a running pwm
    """
    if dutycycle is None : dutycycle=self.dutycycle

    if self.mode == "pwm":
      if dutycycle != self.dutycycle:
        self.pwm.ChangeDutyCycle(dutycycle)
    self._dutycycle=dutycycle


  def initialize(self):

    #To discover the Raspberry Pi board revision:
    self.rpi_revision=GPIO.RPI_REVISION
    
    #To discover the version of RPi.GPIO:
    self.version=GPIO.VERSION


    if self.mode == "poll" or self.mode == "in":
      # set up GPIO output with pull-up control
      #   (pull_up_down be PUD_OFF, PUD_UP or PUD_DOWN, default PUD_OFF)
      if self.pull == "up":
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      elif self.pull == "down":
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
      else:
        print "setto pull a off"
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    if self.mode == "out":
      GPIO.setup(self.channel, GPIO.OUT)
      GPIO.output(self.channel, self.status)
    
    elif self.mode == "pwm":

      GPIO.setup(self.channel, GPIO.OUT)
      self.pwm = GPIO.PWM(self.channel, self.frequency)
      self.pwm.start(self.dutycycle)

    elif self.mode == "poll":
      pass

    elif self.mode == "in":

      if self.bouncetime is None or self.bouncetime == 0:
        print "setto callback"
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

    GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    #self.initialize()
    #GPIO.cleanup(channel=self.channel)

  def manageevent(self,channel):
    print "My Event happen! ",channel
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
      event=False

    self.status=status
    if event:
      try:
        self.myfunction(channel)
      except:
        print "error calling myfunction"

def main():
  import time

  def myfunction(channel):
    print "I get my new pin status : ",channel


  # to use Raspberry BCM pin numbers
  GPIO.setmode(GPIO.BCM)
  dutycycle=0.

  pin18=pin(channel=18,mode="in",pull="up",bouncetime=200,myfunction=myfunction)
#  pin23=pin(channel=23,mode="pwm",frequency=50.,dutycycle=dutycycle)

  while True:
    try:
      time.sleep(3)
      print ">",pin18.status
      continue

      print "I am sleeping ..."
      time.sleep(2)
      print "pin 18 status=",pin18.status
      #pin23.status= not pin23.status()
      dutycycle+=10.
      if dutycycle > 100. :
        dutycycle=0.
      pin23.dutycycle=dutycycle
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

#!/usr/bin/python
# -*- coding: utf-8 -*-
# GPL. (C) 2013 Paolo Patruno.
# Authors: Paolo Patruno <p.patruno@iperbole.bologna.it> 

# This program is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by 
# the Free Software Foundation; either version 2 of the License, or 
# (at your option) any later version. 
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details. 
# 
# You should have received a copy of the GNU General Public License 
# along with this program; if not, write to the Free Software 
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA 
# 

import RPi.GPIO as GPIO
import logging


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
    self.myfunction=myfunction

    #To discover the Raspberry Pi board revision:
    logging.debug("GPIO: GPIO.RPI_REVISION")
    self.rpi_revision=GPIO.RPI_REVISION
    
    #To discover the version of RPi.GPIO:
    logging.debug("GPIO: GPIO.VERSION")
    self.version=GPIO.VERSION
    
    self.initialize()


  @property
  def status(self):

    if self.mode=="poll" or self.mode == "in" or self.mode == "out":
      logging.debug("GPIO: GPIO.input(%s)" % self.channel)
      self._status=GPIO.input(self.channel)
    else:
      self._status=None
    return self._status

  @status.setter
  def status(self, value):

    if self.mode=="out":
      logging.debug("GPIO: GPIO.output(%s,%s)" % (self.channel,value))
      GPIO.output(self.channel, value)
      self._state=value
    else:
      self._status=None
      

  @property
  def mode(self):
    return self._mode

  @mode.setter
  def mode(self, value):
    logging.debug("change properties mode to: %s" % value)

    if not value in ("in","out","poll"):
      logging.warning("mode can be: 'in','out','poll'")
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
    logging.debug("change properties pull to: %s" % value)

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

    if self.mode == "poll" or self.mode == "in":
      # set up GPIO output with pull-up control
      #   (pull_up_down be PUD_OFF, PUD_UP or PUD_DOWN, default PUD_OFF)
      if self.pull == "up":
        logging.debug("GPIO: GPIO.setup(%s,%s,%s)" % (self.channel, GPIO.IN, GPIO.PUD_UP))
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      elif self.pull == "down":
        logging.debug("GPIO: GPIO.setup(%s,%s,%s)" % (self.channel, GPIO.IN, GPIO.PUD_DOWN))
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
      else:
        logging.debug( "setto pull a off")
        logging.debug("GPIO: GPIO.setup(%s,%s,%s)" % (self.channel, GPIO.IN, GPIO.PUD_OFF))
        GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    if self.mode == "out":
      logging.debug("GPIO: GPIO.setup(%s,%s)" % (self.channel, GPIO.OUT))
      GPIO.setup(self.channel, GPIO.OUT)
      logging.debug("GPIO: GPIO.output(%s,%s)" % (self.channel, self.status))
      GPIO.output(self.channel, self.status)
    
    elif self.mode == "pwm":

      logging.debug("GPIO: GPIO.setup(%s,%s)" % (self.channel, GPIO.OUT))
      GPIO.setup(self.channel, GPIO.OUT)
      logging.debug("GPIO: GPIO.PWM(%s,%s)" % (self.channel, self.frequency))
      self.pwm = GPIO.PWM(self.channel, self.frequency)
      logging.debug("GPIO: start PWM(%s)" % (self.dutycycle))
      self.pwm.start(self.dutycycle)

    elif self.mode == "poll":
      pass

    elif self.mode == "in":

      if self.bouncetime is None or self.bouncetime == 0:
        logging.info("set callback: %s" % self.channel)
        logging.info( "GPIO: GPIO.add_event_detect(%s,%s)" % (self.channel, GPIO.BOTH))
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

        logging.info("set callback: %s bouncetime: %s" % (self.channel,self.bouncetime))
        logging.info("GPIO: GPIO.add_event_detect(%s,%s,%s)" % (self.channel, GPIO.BOTH,str(self.bouncetime)))
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
    logging.debug( "removeevent: %s" % self.channel)
    logging.debug("GPIO: GPIO.remove_event_detect(%s)" % self.channel)
    GPIO.remove_event_detect(self.channel)


  def delete(self):
  
    self.stoppwm()
    self.removeevent()

    self.mode="in"
    self.pull=None

    logging.debug("GPIO: GPIO.setup(%s,%s,%s)" % (self.channel, GPIO.IN,GPIO.PUD_OFF))
    GPIO.setup(self.channel, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    #self.initialize()
    #GPIO.cleanup(channel=self.channel)

  def manageevent(self,channel):
    logging.debug("My Event happen! %s" %channel)
    if self.channel != channel:
      logging.warning( "mmm... somethink is wrong ! channel is not coerent.")
      return

    logging.debug("GPIO: GPIO.input(%s)" % (self.channel))
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
        self.myfunction(channel,self)
      except:
        logging.debug("error calling myfunction")

def main():
  import time

  def myfunction(channel,pin):
    logging.info("I get my new pin status : %s = %d" %(channel,pin.status))
    print "I get my new pin status : %s = %d" %(channel,pin.status)


  # to use Raspberry BCM pin numbers
  GPIO.setmode(GPIO.BCM)
  dutycycle=0.

  pin18=pin(channel=18,mode="in",pull="up",bouncetime=200,myfunction=myfunction)
#  pin23=pin(channel=23,mode="pwm",frequency=50.,dutycycle=dutycycle)

  while True:
    try:
      time.sleep(3)
      #print ">",pin18.status
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

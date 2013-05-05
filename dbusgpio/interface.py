#!/usr/bin/env python
# -*- coding: utf-8 -*-
# GPL. (C) 2013 Paolo Patruno.

# Authors: Paolo Patruno <p.patruno@iperbole.bologna.it> 

import sys, time, thread
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import logging
import signal
import managepin
import RPi.GPIO as GPIO

BOARDNAME="myboard"
IFACE="org.gpio"


class NotSupportedException(dbus.DBusException):
  _dbus_error_name = 'org.gpio.NotSupported'

def interface2pin(interface):
  word=interface.split(".")
  return int(word[len(word)-1][7:])

class gpio(dbus.service.Object):
    ''' The base object of an GPIO management'''

    __root_interface = IFACE+"."+BOARDNAME
    __path = "/org/gpio/"+BOARDNAME
    __iface= "org.gpio."+BOARDNAME
    __name = __iface + ".Pins"

    __introspect_interface = "org.freedesktop.DBus.Introspectable"
    __prop_interface = dbus.PROPERTIES_IFACE

    def __init__(self,pinlist=(18,),busaddress=None,loop=None):

      self.pinlist=pinlist
      self.running=False

      if busaddress is None:
        self._bus = dbus.SessionBus()
        logging.debug( "connect to session bus")
      else:
        logging.debug( "connect to ",busaddress)
        self._bus =dbus.bus.BusConnection(busaddress)

      dbus.service.Object.__init__(self, self._bus,
                                     gpio.__path)


      self._uname = self._bus.get_unique_name()
      self._dbus_obj = self._bus.get_object("org.freedesktop.DBus",
                                            "/org/freedesktop/DBus")
      self._dbus_obj.connect_to_signal("NameOwnerChanged",
                                       self._name_owner_changed_callback,
                                       arg0=self.__name)
      self.acquire_name()

        # to use Raspberry BCM pin numbers
      GPIO.setmode(GPIO.BCM)

      self.pins={}


      __root_props = {
        "RpiRevision": (self.__getRpiRevision,None),
        "Version": (self.__getVersion,None),
        "Running": (self.__getRunning,None),
        }

      self.__prop_mapping = {
        self.__root_interface: __root_props,
        }

      for pin in self.pinlist:
        channel_interface=self.__root_interface+".pins.channel"+str(pin)

        __channel_props = {
          "Mode":       (self.__getMode,       self.__setMode),
          "Status":     (self.__getStatus,     self.__setStatus),
          "Pull":       (self.__getPull,       self.__setPull),
          "Frequency":  (self.__getFrequency,  self.__setFrequency),
          "Dutycycle":  (self.__getDutycycle,  self.__setDutycycle),
          "Bouncetime": (self.__getBouncetime, self.__setBouncetime),
          }

        self.__prop_mapping[channel_interface]= __channel_props

      self.loop=loop


    def _name_owner_changed_callback(self, name, old_owner, new_owner):
        logging.debug( "_name_owner_changed_callback")
        if name == self.__name and old_owner == self._uname and new_owner != "":
            try:
                pid = self._dbus_obj.GetConnectionUnixProcessID(new_owner)
            except:
                pid = None
            logging.debug("Replaced by %s (PID %s)" % (new_owner, pid or "unknown"))

            for pin in self.pins.iterkeys():
              self.pins[pin].delete()
            self.pins={}

    def acquire_name(self):
        self._bus_name = dbus.service.BusName(gpio.__name,
                                              bus=self._bus,
                                              allow_replacement=True,
                                              replace_existing=True)
    def release_name(self):
        if hasattr(self, "_bus_name"):
            del self._bus_name


    def __getRpiRevision(self):
      return self.pins[self.pins.keys()[0]].rpi_revision

    def __getVersion(self):
      return self.pins[self.pins.keys()[0]].version

    def __getRunning(self):
      return self.running 


    def __getMode(self,pin):
      return self.pins[str(pin)].mode

    def __setMode(self,pin,mode):
      self.pins[str(pin)].mode=mode

    def __getStatus(self,pin):
      return self.pins[str(pin)].status

    def __setStatus(self,pin,status):
      self.pins[str(pin)].status=status

    def __getPull(self,pin):
      return str(self.pins[str(pin)].pull)

    def __setPull(self,pin,pull):
      self.pins[str(pin)].pull=pull
      return None

    def __getFrequency(self,pin):
      return dbus.Double(self.pins[str(pin)].frequency)

    def __setFrequency(self,pin,status):
      self.pins[str(pin)].frequency=frequency

    def __getDutycycle(self,pin):
      return dbus.Double(self.pins[str(pin)].dutycycle)

    def __setDutycycle(self,pin,status):
      self.pins[str(pin)].dutycycle=dutycycle

    def __getBouncetime(self,pin):
      return dbus.Int64(self.pins[str(pin)].bouncetime)

    def __setBouncetime(self,pin,status):
      self.pins[str(pin)].bouncetime=bouncetime



    @dbus.service.method(__introspect_interface)
    def Introspect(self):

      # python dbus bindings don't include annotations and properties
      GPIO_INTROSPECTION = """<node name=\""""+self.__root_interface+"""\">
  <interface name="org.freedesktop.DBus.Introspectable">
    <method name="Introspect">
      <arg direction="out" name="xml_data" type="s"/>
    </method>
  </interface>
  <interface name="org.freedesktop.DBus.Properties">
    <method name="Get">
      <arg direction="in" name="interface_name" type="s"/>
      <arg direction="in" name="property_name" type="s"/>
      <arg direction="out" name="value" type="v"/>
    </method>
    <method name="GetAll">
      <arg direction="in" name="interface_name" type="s"/>
      <arg direction="out" name="properties" type="a{sv}"/>
    </method>
    <method name="Set">
      <arg direction="in" name="interface_name" type="s"/>
      <arg direction="in" name="property_name" type="s"/>
      <arg direction="in" name="value" type="v"/>
    </method>
    <signal name="PropertiesChanged">
      <arg name="interface_name" type="s"/>
      <arg name="changed_properties" type="a{sv}"/>
      <arg name="invalidated_properties" type="as"/>
    </signal>
  </interface>
  <interface name=\""""+self.__root_interface+"""\">
    <method name="Raise"/>
    <method name="Quit"/>
    <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
    <property name="RpiRevision" type="s" access="read"/>
    <property name="Version" type="s" access="read"/>
    <property name="Running" type="b" access="read"/>
  </interface>"""
  
      for pin in self.pinlist:
        GPIO_INTROSPECTION += """
  <interface name=\""""+self.__root_interface+".pins.channel"+str(pin)+"""\">
    <property name="Mode" type="s" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Status" type="b" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Pull" type="s" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Frequency" type="d" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Dutycycle" type="d" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Bouncetime" type="i" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
  </interface>"""

      GPIO_INTROSPECTION += """
</node>
"""
      return GPIO_INTROSPECTION

    @dbus.service.signal(__prop_interface, signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed_properties,
                          invalidated_properties):
      logging.debug( "property changed")
      print interface, changed_properties,invalidated_properties

    @dbus.service.method(__prop_interface,
                         in_signature="ss", out_signature="v")
    def Get(self, interface, prop):
        getter, setter = self.__prop_mapping[interface][prop]
        if callable(getter):
          if interface.startswith(self.__root_interface+".pins.channel"):
            return getter(interface2pin(interface))
          else:
            return getter()
        return getter

    @dbus.service.method(__prop_interface,
                         in_signature="ssv", out_signature="")
    def Set(self, interface, prop, value):
        getter, setter = self.__prop_mapping[interface][prop]
        if setter is not None:
          if interface.startswith(self.__root_interface+".pins.channel"):
            setter(interface2pin(interface),value)
          else:
            setter(value)

          logging.debug('Updated property: %s = %s' % (prop, value))
          self.PropertiesChanged(interface, {prop: value}, [])
          #return value

            
    @dbus.service.method(__prop_interface,
                         in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        read_props = {}
        props = self.__prop_mapping[interface]
        for key, (getter, setter) in props.iteritems():
            if callable(getter):
              if interface.startswith(self.__root_interface+".pins.channel"):
                getter = getter(interface2pin(interface))
              else:
                getter = getter()
            read_props[key] = getter
        return read_props

    def update_property(self, interface, prop):
      logging.debug("update_property")
      getter, setter = self.__prop_mapping[interface][prop]
      logging.debug( "getter, setter",getter, setter )

      if callable(getter):
        if interface.startswith(self.__root_interface+".pins.channel"):
          value = getter(interface2pin(interface))
        else:
          value = getter()
      else:
        value = getter
      logging.debug('Updated property: %s = %s' % (prop, value))
      self.PropertiesChanged(interface, {prop: value}, [])
      return value

    def update_property_pin(self,channel,pin):
      channel_interface=self.__root_interface+".pins.channel"+str(channel)
      logging.debug( "update_property_pin : %s" % channel_interface )
      self.update_property(channel_interface,"Status")

    @dbus.service.method(IFACE+"."+BOARDNAME)
    def Raise(self):
      for pin in self.pinlist:
        logging.debug( "carico in %s funzione: %s" % (pin, str(self.update_property_pin)))
        self.pins[str(pin)]=managepin.pin(channel=pin,mode="in",
            pull="up",frequency=50.,dutycycle=50.,bouncetime=10,
                                          myfunction=self.update_property_pin)
      self.running=True

    @dbus.service.method(IFACE+"."+BOARDNAME)
    def Quit(self):
      for pin in self.pins.iterkeys():
        self.pins[pin].delete()
      self.pins={}
      self.loop.quit()
      self.release_name()
      self.running=False

# Handle signals more gracefully
    def handle_sigint(self,signum, frame):
      logging.debug('Caught SIGINT, exiting.')
      self.Quit()

    def falsesignal(self):

      print "try to send emulated software signal"
      try:
        self.update_property_pin(18,None)
        print "false signal sended"
      except:
        print "error sending false signal"
      finally:
        return True


def main(pinlist=(18,),busaddress=None):  

  # Use logging for ouput at different *levels*.
  #
  logging.getLogger().setLevel(logging.INFO)
  log = logging.getLogger("dbusgpio")
  handler = logging.StreamHandler(sys.stderr)
  log.addHandler(handler)
 
#  logging.basicConfig(level=logging.INFO,)

#  try:
#    os.chdir(cwd)
#  except:
#    pass


  gobject.threads_init()

  try:  
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    loop = gobject.MainLoop()

    # Export our DBUS service
    #if not dbus_service:
    #dbus_service = GPIOInterface()
    #else:
    # Add our service to the session bus
    #  dbus_service.acquire_name()

    #gobject.timeout_add( 1000,ap.player.printinfo)

    gp = gpio(pinlist=pinlist,busaddress=busaddress,loop=loop)

    signal.signal(signal.SIGINT, gp.handle_sigint)

    #gp.Raise()
    #gobject.timeout_add(5000,gp.falsesignal)

    loop.run()

    # Clean up
    logging.debug('Exiting')


  except KeyboardInterrupt :
    # Clean up
    logging.debug('Keyboard Exiting')
    loop.quit()
    gp.release_name()

#  thread.start_new_thread(mp.loop, ())
#  object.threads_init()
#  context = loop.get_context()
#  gobject.MainLoop().run()
#  while True:
#    context.iteration(True) 

if __name__ == '__main__':

  main(busaddress='tcp:host=192.168.1.180,port=1234')# (this code was run as script)


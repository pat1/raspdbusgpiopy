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


IFACE="org.gpio.myboard"
root_interface = IFACE
pins_interface = IFACE+".Pins"
channel18_interface = pins_interface+".channel18"


# python dbus bindings don't include annotations and properties
GPIO_INTROSPECTION = """<node name=\""""+root_interface+"""\">
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
  <interface name=\""""+root_interface+"""\">
    <method name="Raise"/>
    <method name="Quit"/>
    <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
    <property name="RpiRevision" type="s" access="read"/>
    <property name="Version" type="s" access="read"/>
  </interface>
  <interface name=\""""+channel18_interface+"""\">
    <property name="state" type="b" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
  </interface>
</node>"""


print GPIO_INTROSPECTION

class NotSupportedException(dbus.DBusException):
  _dbus_error_name = 'org.gpio.NotSupported'


class gpio(dbus.service.Object):
    ''' The base object of an GPIO management'''

    __name = "org.gpio.myboard.Pins"
    __path = "/org/gpio/myboard"
    __introspect_interface = "org.freedesktop.DBus.Introspectable"
    __prop_interface = dbus.PROPERTIES_IFACE

    def __init__(self,busaddress=None):

        if busaddress is None:
          self._bus = dbus.SessionBus()
        else:
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

        self.pin18=managepin.pin(channel=18)


    def _name_owner_changed_callback(self, name, old_owner, new_owner):
        if name == self.__name and old_owner == self._uname and new_owner != "":
            try:
                pid = self._dbus_obj.GetConnectionUnixProcessID(new_owner)
            except:
                pid = None
            logging.info("Replaced by %s (PID %s)" % (new_owner, pid or "unknown"))

            self.pin18.delete()

    def acquire_name(self):
        self._bus_name = dbus.service.BusName(gpio.__name,
                                              bus=self._bus,
                                              allow_replacement=True,
                                              replace_existing=True)
    def release_name(self):
        if hasattr(self, "_bus_name"):
            del self._bus_name



    def __getRpiRevision(self):
        return self.pin18.rpi_revision

    def __getVersion(self):
        self.pin18.version


    def __getStatus(self):
        return self.pin18.getstatus()

    def __setStatus(self,status):
        self.pin18.setstatus(status)


    __root_props = {
        "Quit": (False,None),
        "Raise": (False,None),
    }

    __pins_props = {
        "RpiRevision": (__getRpiRevision,None),
        "Version": (__getVersion,None),
    }

    __channel18_props = {
        "Status": (__getStatus, __setStatus),
    }

    __prop_mapping = {
        root_interface: __root_props,
        pins_interface: __pins_props,
        channel18_interface: __channel18_props,
    }


    @dbus.service.method(__introspect_interface)
    def Introspect(self):
        return GPIO_INTROSPECTION

    @dbus.service.signal(__prop_interface, signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed_properties,
                          invalidated_properties):
        pass

    @dbus.service.method(__prop_interface,
                         in_signature="ss", out_signature="v")
    def Get(self, interface, prop):
        getter, setter = self.__prop_mapping[interface][prop]
        if callable(getter):
            return getter(self)
        return getter

    @dbus.service.method(__prop_interface,
                         in_signature="ssv", out_signature="")
    def Set(self, interface, prop, value):
        getter, setter = self.__prop_mapping[interface][prop]
        if setter is not None:
            setter(self,value)

    @dbus.service.method(__prop_interface,
                         in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        read_props = {}
        props = self.__prop_mapping[interface]
        for key, (getter, setter) in props.iteritems():
            if callable(getter):
                getter = getter(self)
            read_props[key] = getter
        return read_props

    def update_property(self, interface, prop):
        getter, setter = self.__prop_mapping[interface][prop]
        if callable(getter):
            value = getter(self)
        else:
            value = getter
        logging.debug('Updated property: %s = %s' % (prop, value))
        self.PropertiesChanged(interface, {prop: value}, [])
        return value

    @dbus.service.method(IFACE)
    def Raise(self):
      pass

    @dbus.service.method(IFACE)
    def Quit(self):
      pass


# Handle signals more gracefully
    def handle_sigint(self,signum, frame):
      logging.debug('Caught SIGINT, exiting.')
      self.Quit()


def main(busaddress=None,myaudiosink=None):  

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

    gp = gpio(busaddress=busaddress)

    signal.signal(signal.SIGINT, gp.handle_sigint)

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


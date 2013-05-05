#!/usr/bin/env python
# -*- coding: utf-8 -*-
# GPL. (C) 2013 Paolo Patruno.

# Authors: Paolo Patruno <p.patruno@iperbole.bologna.it> 

import dbus
import dbus.mainloop.glib
import gobject


def poweroff():

    bus = dbus.SystemBus()
    ck = bus.get_object('org.freedesktop.ConsoleKit',
                        '/org/freedesktop/ConsoleKit/Manager')
    
    p = dbus.Interface(ck,dbus_interface='org.freedesktop.ConsoleKit.Manager')
    p.Stop()


busaddress='tcp:host=192.168.1.180,port=1234'

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

if busaddress is None:
    bus = dbus.SystemBus()
else:
    bus = dbus.bus.BusConnection(busaddress)

proxy = bus.get_object('org.gpio.myboard.Pins','/org/gpio/myboard')
properties_manager = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
board_manager= dbus.Interface(proxy, 'org.gpio.myboard')

if not properties_manager.Get('org.gpio.myboard', 'Running'):
# start management of board pins
    board_manager.Raise('org.gpio.myboard')

#pin 18 in
properties_manager.Set('org.gpio.myboard.pins.channel18','Pull',"up")
properties_manager.Set('org.gpio.myboard.pins.channel18','Mode',"in")
print "18 status=", properties_manager.Get('org.gpio.myboard.pins.channel18','Status')


def signal_handler(interface,properties,arg0):
    print "signal received"
    print "interface=",interface
    for prop in properties.keys():
        print prop, properties[prop]
        if prop == "Status" and properties[prop] == 0 :
            poweroff()
    #print arg0

bus.add_signal_receiver(signal_handler, dbus_interface = dbus.PROPERTIES_IFACE, signal_name = "PropertiesChanged")

try:  
    loop = gobject.MainLoop()
    loop.run()

except KeyboardInterrupt :
    # exit the management daemon
    board_manager.Quit('org.gpio.myboard')

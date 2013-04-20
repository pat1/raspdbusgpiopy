#!/usr/bin/env python
# -*- coding: utf-8 -*-
# GPL. (C) 2013 Paolo Patruno.

# Authors: Paolo Patruno <p.patruno@iperbole.bologna.it> 

import sys
import dbus
import dbus.service
import dbus.mainloop.glib
import logging
import signal
import time
import gobject

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


print "version=", properties_manager.Get('org.gpio.myboard', 'Version')
print "rpi revision=", properties_manager.Get('org.gpio.myboard', 'RpiRevision')


##pin 18 poll
#properties_manager.Set('org.gpio.myboard.pins.channel18','Mode',"pool")
#print "18 status=", properties_manager.Get('org.gpio.myboard.pins.channel18','Status')

#pin 23 out
#properties_manager.Set('org.gpio.myboard.pins.channel23','Mode',"out")
#properties_manager.Set('org.gpio.myboard.pins.channel23','Status',True)
#time.sleep(3)
#properties_manager.Set('org.gpio.myboard.pins.channel23','Status',False)


#pin 18 in
properties_manager.Set('org.gpio.myboard.pins.channel18','Pull',"up")
properties_manager.Set('org.gpio.myboard.pins.channel18','Mode',"in")
print "18 status=", properties_manager.Get('org.gpio.myboard.pins.channel18','Status')


def signal_handler():
    print "signal received"

proxy.connect_to_signal(None, signal_handler, dbus_interface=dbus.PROPERTIES_IFACE, arg0=None)
#proxy.connect_to_signal("PropertiesChanged", signal_handler, dbus_interface=dbus.PROPERTIES_IFACE, arg0=None)

loop = gobject.MainLoop()
loop.run()


# exit the management daemon
board_manager.Quit('org.gpio.myboard')

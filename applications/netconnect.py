#!/usr/bin/env python
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

import sys
import dbus
import dbus.service
import dbus.mainloop.glib
import logging
import signal
import time
import gobject

busaddress1='tcp:host=192.168.1.181,port=1234'
busaddress2='tcp:host=192.168.1.180,port=1234'

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus1 = dbus.bus.BusConnection(busaddress1)
bus2 = dbus.bus.BusConnection(busaddress2)

proxy1 = bus1.get_object('org.gpio.myboard.Pins','/org/gpio/myboard')
properties_manager1 = dbus.Interface(proxy1, 'org.freedesktop.DBus.Properties')
board_manager1= dbus.Interface(proxy1, 'org.gpio.myboard')

proxy2 = bus2.get_object('org.gpio.myboard.Pins','/org/gpio/myboard')
properties_manager2 = dbus.Interface(proxy2, 'org.freedesktop.DBus.Properties')
board_manager2= dbus.Interface(proxy2, 'org.gpio.myboard')

# start management of board pins
if not properties_manager1.Get('org.gpio.myboard', 'Running'):
    board_manager1.Raise('org.gpio.myboard')

if not properties_manager2.Get('org.gpio.myboard', 'Running'):
    board_manager2.Raise('org.gpio.myboard')

#pin 18 board 1 in
properties_manager1.Set('org.gpio.myboard.pins.channel18','Pull',"up")
properties_manager1.Set('org.gpio.myboard.pins.channel18','Mode',"in")
print "18 status=", properties_manager1.Get('org.gpio.myboard.pins.channel18','Status')

#pin 18 board 2 out
properties_manager2.Set('org.gpio.myboard.pins.channel18','Mode',"out")


def signal_handler(interface,properties,arg0):
    print "signal received from board 1"
    if interface == "org.gpio.myboard.pins.channel18":
        for prop in properties.keys():
            print prop, properties[prop]
            if prop == "Status":
                #pin 23 out to the same status of board 1
                properties_manager2.Set(interface,prop,properties[prop])

bus1.add_signal_receiver(signal_handler, dbus_interface = dbus.PROPERTIES_IFACE, signal_name = "PropertiesChanged")

try:  
    loop = gobject.MainLoop()
    loop.run()

except KeyboardInterrupt :
    # exit the management daemon
    #board_manager1.Quit('org.gpio.myboard')
    #board_manager2.Quit('org.gpio.myboard')
    print "Exiting"

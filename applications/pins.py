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



def signal_handler(interface,properties,arg0):
    print "signal received"
    print "interface=",interface
    for prop in properties.keys():
        print prop, properties[prop]
    #print arg0

bus.add_signal_receiver(signal_handler, dbus_interface = dbus.PROPERTIES_IFACE, signal_name = "PropertiesChanged")


#def signal_handler_all(arg1,arg2,arg3,dbus_interface,member):
#    print "signal received"
#    print arg1,arg2,arg3,dbus_interface,member
#
#proxy.connect_to_signal("PropertiesChanged", signal_handler, dbus_interface=dbus.PROPERTIES_IFACE, arg0=None)
#lets make a catchall
#bus.add_signal_receiver(signal_handler_all, interface_keyword='dbus_interface', member_keyword='member')
#bus.add_signal_receiver(catchall_testservice_interface_handler, dbus_interface = "com.example.TestService", message_keyword='dbus_message')


try:  
    loop = gobject.MainLoop()
    loop.run()

except KeyboardInterrupt :
    # exit the management daemon
    board_manager.Quit('org.gpio.myboard')

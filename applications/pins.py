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

busaddress='tcp:host=192.168.1.180,port=1234'

#bus = dbus.SystemBus()
bus = dbus.bus.BusConnection(busaddress)

proxy = bus.get_object('org.gpio.myboard.Pins','/org/gpio/myboard')
properties_manager = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
#properties_manager.Set('org.gpio.myboard', 'Version', 100.0)
version = properties_manager.Get('org.gpio.myboard', 'Version')
print version


channel18_manager= dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')

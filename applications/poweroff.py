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


def poweroff():

    bus = dbus.SystemBus()
    ck = bus.get_object('org.freedesktop.ConsoleKit',
                        '/org/freedesktop/ConsoleKit/Manager')
    
    p = dbus.Interface(ck,dbus_interface='org.freedesktop.ConsoleKit.Manager')
    
    print  p.Stop()


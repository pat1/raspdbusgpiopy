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

# python dbus bindings don't include annotations and properties
GPIO_INTROSPECTION = """<node name="/org/gpio/Pins">
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
  <interface name="org.gpio.Pins">
    <method name="Raise"/>
    <method name="Quit"/>
    <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
    <property name="RpiRevision" type="s" access="read"/>
    <property name="Version" type="s" access="read"/>
  </interface>
  <interface name="org.gpio.Pins.Channel18">
    <method name="State"/>
    <method name="SetPosition">
      <arg direction="in" name="TrackId" type="o"/>
      <arg direction="in" name="Position" type="x"/>
    </method>
    <method name="OpenUri">
      <arg direction="in" name="Uri" type="s"/>
    </method>
    <signal name="Seeked">
      <arg name="Position" type="x"/>
    </signal>
    <property name="PlaybackStatus" type="s" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="LoopStatus" type="s" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Rate" type="d" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Shuffle" type="b" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Metadata" type="a{sv}" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="Volume" type="d" access="readwrite">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
    </property>
    <property name="Position" type="x" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
    </property>
    <property name="MinimumRate" type="d" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="MaximumRate" type="d" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="CanGoNext" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="CanGoPrevious" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="CanPlay" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="CanPause" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="CanSeek" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
    </property>
    <property name="CanControl" type="b" access="read">
      <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="false"/>
    </property>
  </interface>
  <interface name="org.gpio.MediaPlayer2.TrackList">
    <property access="read" type="b" name="CanEditTracks" />
    <method name="GoTo">
      <arg direction="in"  type="s" name="trackid" />
    </method>
    <property access="read" type="as" name="Tracks" />
    <method name="AddTrack">
      <arg direction="in"  type="s" name="uri" />
      <arg direction="in"  type="s" name="aftertrack" />
      <arg direction="in"  type="b" name="setascurrent" />
    </method>
    <method name="GetTracksMetadata">
      <arg direction="in"  type="as" name="trackids" />
      <arg direction="out" type="aa{sv}" />
    </method>
    <method name="RemoveTrack">
      <arg direction="in"  type="s" name="trackid" />
    </method>
    <signal name="TrackListReplaced">
      <arg type="ao" />
      <arg type="o" />
    </signal>
    <signal name="TrackAdded">
      <arg type="a{sv}" />
      <arg type="o" />
    </signal>
    <signal name="TrackRemoved">
      <arg type="o" />
    </signal>
    <signal name="TrackMetadataChanged">
      <arg type="o" />
      <arg type="a{sv}" />
    </signal>
  </interface>
</node>"""

PLAYER_IFACE="org.gpio.MediaPlayer2.Player"
TRACKLIST_IFACE="org.gpio.MediaPlayer2.TrackList"
IFACE="org.gpio.MediaPlayer2"

class NotSupportedException(dbus.DBusException):
  _dbus_error_name = 'org.gpio.NotSupported'


class gpio(dbus.service.Object):
    ''' The base object of an GPIO management'''

    __name = "org.gpio.MediaPlayer2.AutoPlayer"
    __path = "/org/gpio/MediaPlayer2"
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

    def _name_owner_changed_callback(self, name, old_owner, new_owner):
        if name == self.__name and old_owner == self._uname and new_owner != "":
            try:
                pid = self._dbus_obj.GetConnectionUnixProcessID(new_owner)
            except:
                pid = None
            logging.info("Replaced by %s (PID %s)" % (new_owner, pid or "unknown"))
            self.player.loop.quit()

    def acquire_name(self):
        self._bus_name = dbus.service.BusName(gpio.__name,
                                              bus=self._bus,
                                              allow_replacement=True,
                                              replace_existing=True)
    def release_name(self):
        if hasattr(self, "_bus_name"):
            del self._bus_name


    def __PlaybackStatus(self):
        return self.player.playmode

    def __Metadata(self):

      meta=self.GetTracksMetadata((self.player.playlist.current,))
      if len(meta) > 0:
        return dbus.Dictionary(meta[0], signature='sv') 
      else:
        return dbus.Dictionary({}, signature='sv') 


    def __Position(self):
      position = self.player.position()
      if position is None:
        return dbus.Int64(0)
      else:
        return dbus.Int64(position)

    def __CanPlay(self):
        if self.player.playlist.current is None :
            return False
        else:
            return True

    def __Tracks(self):

        tracks=dbus.Array([], signature='s')
        for track in self.player.playlist:
            tracks.append(track)
        return tracks


    __root_interface = IFACE
    __root_props = {
        "CanQuit": (True, None),
        "CanRaise": (False, None),
        "DesktopEntry": ("gpio", None),
        "HasTrackList": (True, None),
        "SupportedUriSchemes": (dbus.Array(signature="s"), None),
        "SupportedMimeTypes": (dbus.Array(signature="s"), None),
        "CanSetFullscreen": (False, None),
    }

    __player_interface = PLAYER_IFACE
    __player_props = {
        "PlaybackStatus": (__PlaybackStatus, None),
        "LoopStatus": (False, None),
        "Rate": (1.0, None),
        "Shuffle": (False, None),
        "Metadata": (__Metadata, None),
        "Volume": (1.0, None),
        "Position": (__Position, None),
        "MinimumRate": (1.0, None),
        "MaximumRate": (1.0, None),
        "CanGoNext": (True, None),
        "CanGoPrevious": (True, None),
        "CanPlay": (__CanPlay, None),
        "CanPause": (True, None),
        "CanSeek": (True, None),
        "CanControl": (True, None),
    }

    __tracklist_interface = TRACKLIST_IFACE
    __tracklist_props = {
        "CanEditTracks": (True, None),
        "Tracks": (__Tracks, None),
}

    __prop_mapping = {
        __player_interface: __player_props,
        __root_interface: __root_props,
        __tracklist_interface: __tracklist_props,
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


    def attach_player(self,player):
        self.player=player


    @dbus.service.signal(PLAYER_IFACE,signature='x')
    def Seeked(self, position):
      logging.debug("Seeked to %i" % position)
      return float(position)

    # TrackAdded 	(a{sv}: Metadata, o: AfterTrack) 	
    @dbus.service.signal(TRACKLIST_IFACE,signature='a{sv}o')
    def TrackAdded(self, metadata,aftertrack):
      logging.debug("TrackAdded to %s" % aftertrack)
      pass

    # TrackRemoved 	(o: TrackId) 	
    @dbus.service.signal(TRACKLIST_IFACE,signature='o')
    def TrackRemoved(self,trackid):
      logging.debug("TrackRemoved %s" % trackid)

# here seem pydbus bug 
# disabled for now

#process 22558: arguments to dbus_message_iter_append_basic() were incorrect, assertion "_dbus_check_is_valid_path (*string_p)" failed in file dbus-message.c line 2531.
#This is normally a bug in some application using the D-Bus library.
#  D-Bus not built with -rdynamic so unable to print a backtrace
#Annullato (core dumped)

      try:
        obp=dbus.ObjectPath("/org/gpio/MediaPlayer2/TrackList/"+trackid)
      except:
        logging.error("building ObjectPath to return in TrackRemoved %s" % trackid)
        obp=dbus.ObjectPath("/org/gpio/MediaPlayer2/TrackList/NoTrack")

      return obp 

    @dbus.service.method(IFACE)
    def Raise(self):
      pass

    @dbus.service.method(IFACE)
    def Quit(self):
      self.player.exit()
      self.release_name()

    @dbus.service.method(PLAYER_IFACE)
    def Next(self):
      self.player.next()

    @dbus.service.method(PLAYER_IFACE)
    def Previous(self):
      self.player.previous()

    @dbus.service.method(PLAYER_IFACE)
    def Pause(self):
      self.player.pause()

    @dbus.service.method(PLAYER_IFACE)
    def PlayPause(self):
      self.player.playpause()

    @dbus.service.method(PLAYER_IFACE)
    def Stop(self):
      self.player.stop()

    @dbus.service.method(PLAYER_IFACE)
    def Play(self):

      logging.info( "Play")

      self.player.loaduri()
      self.player.play()

    @dbus.service.method(PLAYER_IFACE,in_signature='x')
    def Seek(self,offset):
      position=self.player.seek(offset)
      if position is not None: self.Seeked(position)

    @dbus.service.method(PLAYER_IFACE,in_signature='sx')
    def SetPosition(self,trackid,position):
      self.player.setposition(trackid,position)
      self.Seeked(position)

    @dbus.service.method(PLAYER_IFACE,in_signature='s')
    def OpenUri(self,uri):
      self.player.addtrack(uri,setascurrent=True)
      self.Stop()
      self.Play()


#tracklist

    @dbus.service.method(TRACKLIST_IFACE,in_signature='ssb', out_signature='')
    def AddTrack(self,uri, aftertrack, setascurrent):
        self.player.addtrack(uri, aftertrack, setascurrent)

    @dbus.service.method(TRACKLIST_IFACE,in_signature='s', out_signature='')
    def RemoveTrack(self, trackid):
      if self.player.playlist.current == trackid:
        self.Next()
      self.player.removetrack(trackid)
      #disable for a bug in pydbus ??
      #self.TrackRemoved(trackid)

    @dbus.service.method(TRACKLIST_IFACE,in_signature='s', out_signature='')
    def GoTo(self, trackid):
        self.player.goto(trackid)

    @dbus.service.method(TRACKLIST_IFACE,in_signature='as', out_signature='aa{sv}')
    def GetTracksMetadata(self,trackids):
        metadata=dbus.Array([], signature='aa{sv}')

        return metadata

    def updateinfo(self):
      if self.player.statuschanged:
        self.update_property(PLAYER_IFACE,"PlaybackStatus")
        self.player.statuschanged=False
      self.update_property(PLAYER_IFACE,"Position")
      return True


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

  main()# (this code was run as script)


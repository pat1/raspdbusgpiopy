import os
from configobj import ConfigObj,flatten_errors
from validate import Validator

configspec={}

configspec['dbusgpiod']={}

configspec['dbusgpiod']['logfile']  = "string(default='/tmp/dbusgpiod.log')"
configspec['dbusgpiod']['errfile']  = "string(default='/tmp/dbusgpiod.err')"
configspec['dbusgpiod']['lockfile'] = "string(default='/tmp/dbusgpiod.lock')"
configspec['dbusgpiod']['user']     = "string(default=None)"
configspec['dbusgpiod']['group']    = "string(default=None)"
configspec['dbusgpiod']['busaddress']    = "string(default=None)"

configspec['dbusd']={}

configspec['dbusd']['logfile']  = "string(default='/tmp/dbusd.log')"
configspec['dbusd']['errfile']  = "string(default='/tmp/dbusd.err')"
configspec['dbusd']['lockfile'] = "string(default='/tmp/dbusd.lock')"
configspec['dbusd']['conffile'] = "string(default='dbus-dbusgpio.conf')"
configspec['dbusd']['user']     = "string(default=None)"
configspec['dbusd']['group']    = "string(default=None)"


config    = ConfigObj ('/etc/dbusgpio/dbusgpio-site.cfg',file_error=False,configspec=configspec)

usrconfig = ConfigObj (os.path.expanduser('~/.dbusgpio.cfg'),file_error=False)
config.merge(usrconfig)
usrconfig = ConfigObj ('dbusgpio.cfg',file_error=False)
config.merge(usrconfig)

val = Validator()
test = config.validate(val,preserve_errors=True)
for entry in flatten_errors(config, test):
    # each entry is a tuple
    section_list, key, error = entry
    if key is not None:
       section_list.append(key)
    else:
        section_list.append('[missing section]')
    section_string = ', '.join(section_list)
    if error == False:
        error = 'Missing value or section.'
    print section_string, ' = ', error
    raise error

# section dbusgpiod
logfiledbusgpio              = config['dbusgpiod']['logfile']
errfiledbusgpio              = config['dbusgpiod']['errfile']
lockfiledbusgpio             = config['dbusgpiod']['lockfile']
userdbusgpio                 = config['dbusgpiod']['user']
groupdbusgpio                = config['dbusgpiod']['group']
busaddressdbusgpio           = config['dbusgpiod']['busaddress']

# section dbusd
logfiledbus              = config['dbusd']['logfile']
errfiledbus              = config['dbusd']['errfile']
lockfiledbus             = config['dbusd']['lockfile']
conffiledbus             = config['dbusd']['conffile']
userdbus                 = config['dbusd']['user']
groupdbus                = config['dbusd']['group']



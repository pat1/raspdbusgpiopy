from distutils.core import setup
import os

from distutils.command.build import build as build_
from setuptools.command.develop import develop as develop_
from distutils.core import Command
#from buildutils.cmd import Command
#from distutils.cmd import Command

from dbusgpio import _version_

class distclean(Command):
    description = "remove man pages and *.mo files"
    user_options = []   
    boolean_options = []

    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass

    def run(self):
        import shutil
        from os.path import join
        try:
            shutil.rmtree("man")
        except:
            pass
        for root, dirs, files in os.walk('locale'):
            for name in files:
                if name[-3:] == ".mo":
                    os.remove(join(root, name))

        # remove all the .pyc files
        for root, dirs, files in os.walk(os.getcwd(), topdown=False):
            for name in files:
                if name.endswith('.pyc') and os.path.isfile(os.path.join(root, name)):
                    print 'removing: %s' % os.path.join(root, name)
                    if not(self.dry_run): os.remove(os.path.join(root, name))


class build(build_):

    sub_commands = build_.sub_commands[:]
    sub_commands.append(('compilemessages', None))
    sub_commands.append(('createmanpages', None))

class compilemessages(Command):
    description = "generate .mo files from .po"
    user_options = []   
    boolean_options = []

    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass

    def run(self):
        print "compilemessage function have to be written !!!"

class createmanpages(Command):
    description = "generate man page with help2man"
    user_options = []   
    boolean_options = []

    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass

    def run(self):
        try:
            import subprocess
            subprocess.check_call(["mkdir","-p", "man/man1"])
            subprocess.check_call(["help2man","-N","-o","man/man1/dbusgpiod.1","./dbusgpiod"])
            subprocess.check_call(["gzip","-f", "man/man1/dbusgpiod.1"])
            subprocess.check_call(["help2man","-N","-o","man/man1/dbusd.1","./dbusd"])
            subprocess.check_call(["gzip", "-f","man/man1/dbusd.1"])
        except:
            pass

# Compile the list of files available, because distutils doesn't have
# an easy way to do this.
package_data = []
data_files = []

for dirpath, dirnames, filenames in os.walk('man'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if filenames:
        data_files.append(['share/'+dirpath, [os.path.join(dirpath, f) for f in filenames]])


for dirpath, dirnames, filenames in os.walk('doc'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if filenames:
        data_files.append(['share/autoradio/'+dirpath, [os.path.join(dirpath, f) for f in filenames]])

for dirpath, dirnames, filenames in os.walk('locale'):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if filenames:
        data_files.append(['share/dbusgpio/'+dirpath, [os.path.join(dirpath, f) for f in filenames]])

data_files.append(('/etc/dbusgpio',['dbusgpio-site.cfg']))
data_files.append(('/etc/dbusgpio',['dbus-gpio.conf']))


setup(name='dbusgpio',
      version=_version_,
      description='raspberry dbus daemon interface to gpio',
      author='Paolo Patruno',
      author_email='p.patruno@iperbole.bologna.it',
      platforms = ["any"],
      url='http://raspdbusgpiopy.sf.net',
      cmdclass={'build': build,'compilemessages':compilemessages,'createmanpages':createmanpages,"distclean":distclean},
      packages=['dbusgpio'],
#      package_data={'autoradio.programs': ['fixtures/*.json']},
      scripts=['dbusgpiod','dbusd'],
      data_files = data_files,
      license = "GNU GPL v2",
      requires= [ "RPi.GPIO"],
      long_description="""\
raspberry dbus daemon interface to gpio
"""
     )
     

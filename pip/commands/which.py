import os
import sys
import pip
from pip.log import logger
from pip.basecommand import Command
from pip.exceptions import DistributionNotFound


class WhichCommand(Command):

    name = 'which'
    usage = '%prog [OPTIONS] MODULE_NAME'
    summary = 'Find where a module is installed'

    def __init__(self):
        super(WhichCommand, self).__init__()

        self.parser.add_option('-r', action="store_true", dest="real_path",
            default=False, help="dereference symlinks")
        self.parser.add_option('-b', action="store_true", dest="show_directory",
            default=False, help="show directory instead of filename")
        self.parser.add_option('-i', '--hide-init', action="store_true", dest="hide_init",
            default=False, help="show directory if the module ends in __init__.py")
        self.parser.add_option('--source', action="store_true", dest="find_source",
            default=False, help="find .py files for .pyc/.pyo files")

    def run(self, options, args):
        kwargs = dict((fld, getattr(options, fld)) for fld
            in ('real_path', 'show_directory', 'find_source', 'hide_init'))
        self.identify_modules(*args, **kwargs)

    def identify_module(self, arg, real_path=None, show_directory=None,
        find_source=None, hide_init=None):
        try:
            __import__(arg)
        except Exception, exc:
            raise DistributionNotFound("%s: %s" % (type(exc).__name__, str(exc)))

        mod = sys.modules[arg]
        filename = mod.__file__

        if find_source and (filename.endswith('.pyc') or filename.endswith('.pyo')):
            sourcefile = filename[:-1]
            if os.access(sourcefile, os.F_OK):
                filename = sourcefile

        if real_path:
            filename = os.path.realpath(filename)

        if show_directory or (hide_init and
            os.path.basename(filename).startswith('__init__.')):
            filename = os.path.dirname(filename)

        return filename

    def identify_modules(self, *args, **kwargs):
        if len(args) == 1:
            path_template = "%(file)s"
            error_template = "Module '%(mod)s' not found (%(error)s)"
        else:
            path_template = "%(mod)s: %(file)s"
            error_template = "%(mod)s: not found (%(error)s)"

        for modulename in args:
            try:
                filepath = self.identify_module(modulename, **kwargs)
            except DistributionNotFound, exc:
                print >>sys.stderr, error_template % {
                    'mod': modulename,
                    'error': str(exc),
                }
            else:
                print path_template % {
                    'mod': modulename,
                    'file': filepath
                }


WhichCommand()

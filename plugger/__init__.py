__author__ = 'stevet'

import sys
import traceback
from maya.api.OpenMaya import MFnPlugin, MPxCommand, MSyntax, MDGModifier, MArgDatabase, MGlobal, MDagModifier, \
    MDistance, MAngle, MTime

__version__ = 0.5


class initializePlugin2(object):
    """
    Proxies the `initializePlugin` method that Maya expects to be present in every plugin file.  If you have import this
    into a class with <PluginMeta> derived classes they will automatically be initialized
    """
    KNOWN = []

    def __init__(self, mObj):
        self.mObject = mObj
        plugin_queue = [i for i in self.KNOWN if
                        i not in (CommandBase, UndoableBase)]
        for plugin in plugin_queue:
            MGlobal.displayInfo("registering plugin %s" % plugin)
            vendor = getattr(plugin, 'VENDOR', 'plugger module')
            version = getattr(plugin, 'VERSION', "0.9")
            apiversion = getattr(plugin, "API_VERSION", "Any")
            plugin_obj = MFnPlugin(mObj, vendor, version, apiversion)
            try:
                plugin_obj.registerCommand(plugin.NAME, plugin.creator,
                                           plugin.syntax)
            except RuntimeError as e:
                MGlobal.displayError("Unable to load plugin %s" % plugin)
                MGlobal.displayError(traceback.format_exc(e))
            finally:
                self.KNOWN.remove(plugin)


class uninitializePlugin2(object):
    """
    Proxies the `initializePlugin` method that Maya expects to be present in every plugin file.  If you have import this
    into a class with <PluginMeta> derived classes they will automatically be initialized
    """
    KNOWN = []

    def __init__(self, mObj):
        self.mObject = mObj
        plugin_queue = [i for i in self.KNOWN if
                        i not in (CommandBase, UndoableBase)]
        for plugin in plugin_queue:
            MGlobal.displayInfo("deregistering plugin %s" % plugin)
            plugin_obj = MFnPlugin(mObj)
            try:
                plugin_obj.deregisterCommand(plugin.NAME)
            except:
                MGlobal.displayError("Unable to unload plugin %s" % plugin)
            finally:
                self.KNOWN.remove(plugin)


def generic_creator(cls):
    """
    instantiate `cls()`.  Automatically added to any class using PluginMeta
    as a metaclass. If the class defines it's own creator() class method,
    that will be used instead.
    """
    return cls()


def generic_syntax(cls):
    """
    Creates a generic syntax object. Automatically added to any class using
    PluginMeta as a metaclass. If the class defines it's own syntax()
    class method, that will be used instead.
    """
    m = MSyntax()
    m.setObjectType(MSyntax.kSelectionList)
    m.useSelectionAsDefault(True)
    return m


class PluginMeta(type):
    """
    Add this metaclass to any class derived from an MPx plugin class to
    automatically register the plugin without the extra boilerplate of
    separate initialize, uninitialize and creator methods.

    sample usage:

        from plugger import *

        class ExamplePlugin(MPxCommand):
            __metaclass__ = PluginMeta
            NAME = 'your_plugin_name'
            VENDOR = 'vendor_string'
            VERSION = '1.0'

            def doIt(self, args):
                print "hello world"


    after loading the plugin:

        # registering plugin <class 'ExamplePlugin'>
        >>> cmds.your_plugin_name()
        # hello world

    """

    def __new__(cls, name, bases, dct):
        new_class = None
        dct['creator'] = dct.get('creator', classmethod(generic_creator))
        dct['syntax'] = dct.get('syntax', classmethod(generic_syntax))
        new_class = type.__new__(PluginMeta, name, bases, dct)
        try:
            cls.register(new_class)
        finally:
            return new_class

    @classmethod
    def register(cls, new_class):
        initializePlugin2.KNOWN.append(new_class)


class CommandBase(MPxCommand):
    """
    Base class for generic MPXCommands
    """
    __metaclass__ = PluginMeta
    NAME = 'generic_plugin'

    def isUndoable(self):
        return False

    def maya_useNewAPI(self):
        return True

    def parse(self, arglist):
        return MArgDatabase(self.syntax(), arglist)


class UndoableBase(CommandBase):
    """
    Base class for Undoable MPXCommands
    """
    NAME = 'undoable_generic_command'

    def __init__(self):
        super(UndoableBase, self).__init__()
        self.modifier = MDagModifier()

    def isUndoable(self):
        return True


class CommandPlugin(object):
    """
    For simple functions apply this decorator to a function to create a
    simple, non-undoable
    MPXCommand plugin

    Example:
         from plugger import   initializePlugin2, uninitializePlugin2,
         CommandPlugin

        @CommandPlugin('first')
        def do_something(args):
            print "executed"


        @CommandPlugin('second')
        def do_something_else(args):
            objects = CommandPlugin.objects(args)
            dagPaths = [objects.getDagPath(i) for i in range(objects.length())]
            for path in dagPaths:
                print path.fullPathName()

    The decorated function will be passed an MArgList containing the
    selection.  The decorated function can ignore this or create an
    MSyntax/MArgDatabase to parse the arugment list. As a convenience the
    CommandPlugin class offers two helper methods, `objects()` and
    `arguments()` which will parse the argument list for simple cases (see
    those functions for more)

    """

    def __init__(self, name):
        self.plugin_name = name

    def __call__(self, fn):
        class Anon(CommandBase):
            NAME = self.plugin_name

            def doIt(self, args):
                fn(args)

        Anon.__name__ = fn.func_code.co_name
        return Anon

    @classmethod
    def arguments(cls, arglist, selection=True):
        """
        Rturn the contents of arglist as a list of strings.  If <selection>
        is True, the arglist will be populated with Maya selection
        """
        syntax = MSyntax()
        syntax.setObjectType(MSyntax.kStringObjects)
        syntax.useSelectionAsDefault(selection)
        adb = MArgDatabase(syntax, arglist)
        return adb.getObjectStrings()

    @classmethod
    def objects(cls, arglist, selection=True):
        """
        Returns the contents of arglist as an MSelectionList. If <selection>
        is True, uses the maya selection as the default.

        Note this does no error handling, if the argList has a bad object
        name a RuntimeError will be raised
        """
        syntax = MSyntax()
        syntax.setObjectType(MSyntax.kSelectionList)
        syntax.useSelectionAsDefault(selection)
        try:
            adb = MArgDatabase(syntax, arglist)
            return adb.getObjectList()
        except RuntimeError as e:
            raise RuntimeError("could not parse argument list",
                               cls.arguments(arglist))


class UndoableCommandPlugin(CommandPlugin):
    """
    Use this decorator to create an undoable plugin function. The function
    must return an MDGmodifier or MDagModifier instance in order to suppport
    the undo functionality
    """

    def __call__(self, fn):
        class UndoAnon(UndoableBase):
            NAME = self.plugin_name

            def __init__(self):
                super(UndoAnon, self).__init__()
                self.dg_modifier = None

            def doIt(self, args):
                self.modifier = fn(args)
                assert isinstance(self.dg_modifer, MDGModifier), \
                    "undoable command  must return an MDGModifier instance"
                self.dg_modifer.doIt()

            def undoIt(self):
                self.modifier.undoIt()

        UndoAnon.__name__ = fn.func_code.co_name
        return UndoAnon





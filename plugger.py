__author__ = 'stevet'

import sys

__version__ = 0.5

class PluginMeta(type):

    def __new__(cls, name, bases, dct):
        new_class = None
        try:
            new_class = type.__new__(PluginMeta, name, bases, dct)
            return new_class
        finally:
            cls.register(new_class)

    @classmethod
    def register(cls, new_class):
        print new_class.__module__
        owning_module = sys.modules[new_class.__module__]
        if owning_module:
            print "I created", new_class, "in", owning_module
            setattr(owning_module, 'plugin_meta', 'created by plugger %s' % __version__)



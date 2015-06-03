from plugger import PluginMeta

class ExampleClass(object):
    __metaclass__ = PluginMeta


    def test(self):
        print self

print plugin_meta
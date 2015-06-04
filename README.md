# plugger
Maya plugin helpers

# What it does
Provides a simplified setup for Maya API2 plugins.  

For very simple commands you can import a decorator which declares and registers a plugin, so a plugin can be as simple as:

    from plugger import initializePlugin2, uninitializePlugin2, CommandPlugin

    @CommandPlugin('hello_world')
    def do_something(args):
        print "Hello Word"
        
This would create a basic MPXPluginCommand object and correctly register it as the `hello_world()` command.  There's also and undoable version, which works the same way. If your function returns an `MDGModifier` or `MDagModifier` it becomes undoable:

  
  from plugger import initializePlugin2, uninitializePlugin2, UndoableCommandPlugin

    @UndoableCommandPlugin('cube')
    def do_something(args):
        mod = MDagModifier()
        mod.createNode('polyCube')
        mod.doIt()
        return mod
  
    

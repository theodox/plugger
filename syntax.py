from maya.api.OpenMaya import MSyntax, MDistance, MAngle, MTime, MArgList, MArgDatabase
import inspect

class SyntaxItem(object):
    """
    Represents a flag entry for
    """

    TYPE_MAPPING = {
        None: MSyntax.kNoArg,
        bool: MSyntax.kBoolean,
        long: MSyntax.kLong,
        int: MSyntax.kUnsigned,
        float: MSyntax.kDouble,
        str: MSyntax.kString,
        object: MSyntax.kSelectionItem,
        MDistance: MSyntax.kDistance,
        MAngle: MSyntax.kAngle,
        MTime: MSyntax.kTime
    }


    def __init__(self, fullname, shortname=None, dataType=None, multi = False):
        flag = lambda p: p if p.startswith("-") else "-" + p

        self.long = flag(fullname)
        self.short = flag(shortname) if shortname else self.long[:2]
        try:
            self.dataType = self.TYPE_MAPPING[dataType]
        except KeyError:
            raise ValueError("Unknown Syntax Parameter Type: %s" % dataType)

        self.multi = False

    def insert(self, syntax):
        syntax.addFlag(self.short, self.long, self.dataType)
        if self.multi:
            syntax.makeFlagMultiUse(self.short)
        if self.long == '-query':
            syntax.enableQuery = True
        if self.long == '-edit':
            syntax.enableEdit = True


    def __repr__(self):
        return "{{ %s, %s: %s}}" %(self.short, self.long, self.dataType)


class Flags(object):

    """
    A context manager that allows a shorthand method of creating flags.  Entries are added in the form

        name = type

    where name is python name and type is a type (bool, float, etc or MAngle, MDistance, or MTime). A type of `object`
    is intepreted as a selectionItem. The complete list of mappings is in the TYPE_MAPPINGS dictionary.

    Example usage:

        with Flags() as f:
            boolValue = bool
            uintValue = int
            doubleValue = float

        syntax = f.syntax()

    would create an MSyntax object with these flags:

        -b -bool        kBoolean
        -u -uintValue   kUnsigned
        -d -doubleValue kDouble


    You can customize the short name of the flag using this form:

        with Flags() as f:
            longName = 'ln', str

    which would create an MSyntax like

        -ln  -longName kString

    To create a multi-use flag, enclose the type in square brackets

        with Flags() as f:
            multiInt = [int]

    If the flags 'edit' or 'query' are provided, the final MSyntax will have its edit or query flags enabled by default.

    """

    def __init__(self):
        self.flags = []
        self._syntax = MSyntax()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k, v in  inspect.currentframe().f_back.f_locals.items():
            if v is self:
                continue
            flag = k
            value  = v if isinstance(v, tuple) else (flag[0], v)
            short, typespec = value
            multi = isinstance(typespec, list)
            if multi:
                typespec = typespec[0]
            self.flags.append(SyntaxItem(flag, short, typespec, multi))
        for f in self.flags:
            f.insert(self._syntax)

    def syntax(self):
        return self._syntax


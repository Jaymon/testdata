# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import types
import inspect
import sys
import importlib
import os
import copy

from .compat import *
from .path import get_module_name


###############################################################################
# Supporting classes and methods
###############################################################################

class Mock(object):
    """Do our very best to mock functionality

    This class tries to make it easy to mock an object, and can be used to quickly
    get an object that can match a certain state, it isn't exhaustive and will fail
    things like isinstance checks, but it does it's very best to get you a mocked
    up object that you can use for testing.

    If the given attribute doesn't exist then this will return an instance of self
    so you can chain together objects of any depth with just the first object

    :Example:
        m = Mock(foo=1)
        m.foo() # 1
        m.foo # 1
        m.bar.che.foo # 1

        m = Mock(foo=ValueError("the error you want to raise"))
        m.foo(1, 2) # raises ValueError
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        try:
            v = super(Mock, self).__getattribute__(key)

        except AttributeError:
            return self

        else:
            self._raise_if_error(v)
            #self.__dict__["_raise_if_error"](v)
            return v

    def __getattribute__(self, key):
        if hasattr(type(self), key):
            # this makes sure methods defined on this class get through this call
            return super(Mock, self).__getattribute__(key)

        try:
            v = super(Mock, self).__getattribute__(key)

        except AttributeError:
            return self

        else:
            if v is not None:

                self._raise_if_error(v)
                #self.__dict__["_raise_if_error"](v)

                if not hasattr(v, "__call__"):

                    frames = inspect.stack()
                    frame = frames[1]
                    loc = "\n".join(frame[4])
                    if ".{}(".format(key) in loc or ".{}".format(key) not in loc:

                        # https://stackoverflow.com/questions/2172189/why-i-cant-extend-bool-in-python
                        class_type = type(v) if self._is_type(v, bool) == 0 else object 

                        class MockAttr(class_type):
                            def __new__(cls, *args, **kwargs):
                                try:
                                    return super(MockAttr, cls).__new__(cls, *args, **kwargs)
                                except TypeError:
                                    return super(MockAttr, cls).__new__(cls)

                            def __call__(self, *args, **kwargs):
                                return v

                            def __bool__(self):
                                return bool(v)
                            __nonzero__ = __bool__

                        return MockAttr(v)

        return v

    def _raise_if_error(self, v):
        is_type = self._is_type(v, Exception)
        if is_type == 1:
            raise v

        elif is_type == 2:
            raise v()

#         do_raise = False
#         try:
#             do_raise = isinstance(v, Exception)
# 
#         except TypeError:
#             pass
# 
#         else:
#             if do_raise:
#                 raise v
# 
#         try:
#             do_raise = issubclass(v, Exception)
# 
#         except TypeError:
#             pass
# 
#         else:
#             if do_raise:
#                 raise v()

    def _is_type(self, v, class_types):
        ret = 0
        try:
            if isinstance(v, class_types):
                ret = 1

        except TypeError:
            pass

        if ret == 0:
            try:
                if issubclass(v, class_types):
                    ret = 2

            except TypeError:
                pass

        return ret




###############################################################################
# testdata functions
###############################################################################

def patch_instance(mod, patches=None, **kwargs_patches):
    if not mod:
        raise ValueError("mod is empty")

    if not patches: patches = {}
    patches.update(kwargs_patches) # combine both dicts

    for name, patch in patches.items():
        val = getattr(mod, name, None)
        if inspect.isroutine(val):
            setattr(mod, name, types.MethodType(patch, mod))

        else:
            if name in mod.__class__.__dict__ and inspect.isdatadescriptor(mod.__class__.__dict__[name]):

                # http://stackoverflow.com/questions/30342212/override-attribute-access-precedence-having-a-data-descriptor/30578922#30578922
                monkey_class = patch_class(
                    mod.__class__,
                    **{name: patch}
                )
                mod.__class__ = monkey_class

            else:
                setattr(mod, name, patch)

    return mod


def patch_class(mod, patches=None, **kwargs_patches):
    if not mod:
        raise ValueError("mod is empty")

    if not patches: patches = {}
    patches.update(kwargs_patches) # combine both dicts

    def copy_dict(mod):
        d = {}
        for k, v in mod.__dict__.items():
            if k.startswith("__"):
                d[k] = v
            else:
                if inspect.isroutine(v):
                    d[k] = v

                elif inspect.isdatadescriptor(v):
                    d[k] = v

                else:
                    d[k] = copy.deepcopy(v)
        return d

    class_name = ""
    if is_py2:
        class_name = b'{}Patched'.format(mod.__name__)
    elif is_py3:
        class_name = '{}Patched'.format(mod.__name__)

    # http://stackoverflow.com/questions/9541025/how-to-copy-a-python-class
    mod_patched = type(
        class_name,
        tuple([mod] + list(mod.__bases__)),
        #{k: copy.deepcopy(v) for k, v in mod.__dict__.items()}
        copy_dict(mod)
    )
    for name, patch in patches.items():
        if is_py2:
            o = getattr(mod_patched, name, None)
            if inspect.isroutine(o):
                if inspect.ismethod(o):
                    # https://stackoverflow.com/a/19228282/5006
                    if o.__self__ is mod_patched:
                        if not isinstance(patch, classmethod):
                            patch = classmethod(patch)

                elif isinstance(o, types.FunctionType):
                    # https://stackoverflow.com/a/695694
                    patch = staticmethod(patch)

        setattr(mod_patched, name, patch)

    return mod_patched


def patch_module(mod, patches=None, **kwargs_patches):
    if not mod:
        raise ValueError("mod is empty")

    if not patches: patches = {}
    patches.update(kwargs_patches) # combine both dicts

    deferred_patches = []
    patched_modules = {}

    for name, patch in patches.items():
        if '.' in name:
            # when a module is imported like this, import foo.bar then it is placed
            # as an attribute to the parent module: getattr(getattr(mod, 'foo'), 'bar')
            # this should be useful in eventually supporting this, you can work down the sub
            # attributes and newly import them and patch
            raise RuntimeError("nested modules like {} are not currently supported".format(name))

        else:
            deferred_patches.append((name, patch))

    # now we need to find the full module path so we can reload it
    if inspect.ismodule(mod):
        mod_name = mod.__name__
        mpath = inspect.getsourcefile(mod)
        mfile = mpath

    else:
        mod_name = mod

        # http://stackoverflow.com/questions/4907054/
        def find_mod_path(p):
            if '.' in p:
                p, m = p.rsplit('.', 1)
                imod_path = find_mod_path(p)
                mod_path = os.path.join(imod_path, m)

            else:
                # we fudge the paths a bit to make sure current working directory is
                # also checked
                paths = [os.getcwd()]
                paths.extend(sys.path)
                # imp is deprecated in python 3, see:
                # https://stackoverflow.com/questions/35288021/what-is-the-equivalent-of-imp-find-module-in-importlib
                if is_py2:
                    _, mod_path, _ = imp.find_module(p, paths)

                else:
                    spec = importlib.machinery.PathFinder().find_spec(p, paths)
                    if spec.submodule_search_locations:
                        mod_path = spec.submodule_search_locations[0]
                    else:
                        mod_path = spec.origin

            return mod_path

        mpath = find_mod_path(mod_name)

        mfile = mpath
        # figure out if we have a package or a module and set the appropriate file
        if os.path.isdir(mpath):
            mfile = os.path.join(mpath, '__init__.py')

        else:
            if not mfile.endswith(".py"):
                mfile = '{}.py'.format(mpath)

    mname = get_module_name(prefix=mod_name)
    #mname = '{}_{}'.format(mod_name, get_ascii(8))
    if is_py2:
        m = imp.load_source(mname, mfile)
    else:
        # ugh, this is deprecated in 3.4 (though it isn't throwing a warning
        m = importlib.machinery.SourceFileLoader(mname, mfile).load_module()
        # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly

#         loader = importlib.machinery.SourceFileLoader(mname, mfile)
#         loaded = types.ModuleType(loader.name)
#         m = loader.exec_module(loaded)

    # go through and apply all the patches
    for patch_name, patch in deferred_patches:
        setattr(m, patch_name, patch)

    return m


def patch(mod, patches=None, **kwargs_patches):
    '''
    import module_name and apply the patches to it

    mod -- string|module|class|instance -- the name of the thing you are patching
    patches -- dict -- the keys are functions, classes, or modules that should be
    patched in the module, the value is the patched value you want to replace the
    key with

    return -- module|object -- if you pass in an object, return the object, otherwise
        return the module
    '''
    if isinstance(mod, basestring):
        m = patch_module(mod, patches=patches, **kwargs_patches)

    elif inspect.ismodule(mod):
        m = patch_module(mod, patches=patches, **kwargs_patches)

    elif inspect.isclass(mod):
        m = patch_class(mod, patches=patches, **kwargs_patches)

    else:
        m = patch_instance(mod, patches=patches, **kwargs_patches) 

    return m


def mock_class(name="", **props_and_methods):
    """create a class with the given method and properties

    :param name: string, the name of the class, default is just a random classname
    :param **props_and_methods: dict, keys will be attributes on the object
    :returns: type, the object
    """
    classname = get_classname(name=name)
    return type(ByteString(classname), (object,), props_and_methods)


def mock_instance(name="", **props_and_methods):
    """This is the same as mock_class but returns an instance of that class

    see mock_class() docs"""
    return mock_class(name, **props_and_methods)()


def mock(**props_and_methods):
    """Create a mocked object that tries to be really magical

    This is different than mock_instance because it creates an object that uses a lot
    of magic to try and be a jack of all trades

    :returns: Mock instance
    """
    return Mock(**props_and_methods)




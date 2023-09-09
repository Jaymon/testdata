# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import types
import inspect
import sys
import importlib
import os
import copy
import functools
from contextlib import contextmanager
import asyncio

from .compat import *
from .base import TestData


###############################################################################
# Supporting classes and methods
###############################################################################

class AsyncRunner(object):
    """Wrap an object instance so any async methods called will return their
    actual values, basically, this makes it easier to test async classes and
    methods

    :Example:
        class Foo(object):
            async bar(self, left, right):
                return left + right

        instance = AsyncRunner(Foo())
        print(instance.bar(1, 2)) # 3
    """
    def __init__(self, instance):
        self.instance = instance

    @classmethod
    def normalize(cls, ret):
        """normalize ret to be the actual value

        basically, this will pass through ret or exhaust ret if it is a
        coroutine since the purpose of this method is to get the actual value

        This is a good overview of why the below code is bad and should only
        ever be used in a testing context:

        * https://discuss.python.org/t/calling-coroutines-from-sync-code-2/24093

        :param ret: Any|coroutine
        :returns: Any, the value that ret should be if it was a coroutine
        """
        if asyncio.iscoroutine(ret):
            try:
                loop = asyncio.get_running_loop()

            except RuntimeError:
                ret = asyncio.run(ret)

            else:
                ret = loop.run_until_complete(ret)

        return ret

    @classmethod
    def decorate(cls, func):
        """wrap a callable so it will exhaust a coroutine and return the actual
        value

        :param func: callable
        :returns: callable, the wrapped func
        """
        def decorated(*args, **kwargs):
            ret = cls.normalize(func(*args, **kwargs))
            return ret

        return decorated

    def __getattribute__(self, key):
        """This is where the magic happens, this will check the value returned
        from .instance and wrap it or normalize it"""
        instance = super().__getattribute__("instance")
        v = getattr(instance, key)
        if callable(v):
            decorate = super().__getattribute__("decorate")
            v = decorate(v)

        else:
            normalize = super().__getattribute__("normalize")
            v = normalize(v)

        return v

    def __setattr__(self, key, value):
        try:
            instance = super().__getattribute__("instance")

        except AttributeError:
            super().__setattr__(key, value)

        else:
            setattr(instance, key, value)


class Mock(object):
    """Do our very best to mock functionality

    This class tries to make it easy to mock an object, and can be used to
    quickly get an object that can match a certain state, it isn't exhaustive
    and will fail on things like isinstance checks, but it does it's very best
    to get you a mocked up object that you can use for testing.

    If the given attribute doesn't exist then this will return an instance of
    self so you can chain together objects of any depth with just the first
    object

    At some point in the future this should extend this:
        https://docs.python.org/dev/library/unittest.mock.html

    :Example:
        m = Mock(foo=1)
        m.foo() # 1
        m.foo # 1
        m.bar.che.foo # 1

        m = Mock(foo=ValueError("the error you want to raise"))
        m.foo(1, 2) # raises ValueError
    """
    def __init__(self, patches=None, **kwargs_patches):
        self._patch(patches, **kwargs_patches)

    def __call__(self, *args, **kwargs):
        """if the method doesn't exist then return self so you can do things
        like `Mock(foo=1).bar().che().foo` and have it work similar to 
        `Mock(foo=1).bar.che.foo`
        """
        return self

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
        # this makes sure the methods defined on this class get through this
        # call
        if key.startswith("_") and hasattr(type(self), key):
            return super(Mock, self).__getattribute__(key)

        try:
            v = super(Mock, self).__getattribute__(key)

        except AttributeError:
            # if the attribute doesn't exist then return self so you can do
            # things like `Mock(foo=1).bar.che.foo` and have it work
            return self

        else:
            if v is not None:

                self._raise_if_error(v)

                if not hasattr(v, "__call__"):

                    frames = inspect.stack()
                    frame = frames[1]
                    loc = "\n".join(frame[4]) if frame[4] else ["REPL"]
                    if ".{}(".format(key) in loc or ".{}".format(key) not in loc:

                        # https://stackoverflow.com/questions/2172189/why-i-cant-extend-bool-in-python
                        not_bool = not self._is_instance(v, bool)
                        if not_bool:
                            not_bool = not self._is_subclass(v, bool)

                        #not_bool = (not self._is_instance(v, bool) and not self._is_subclass(v, bool))
                        class_type = type(v) if not_bool else object 

                        class MockAttr(class_type):
                            def __new__(cls, *args, **kwargs):
                                try:
                                    return super(MockAttr, cls).__new__(
                                        cls,
                                        *args,
                                        **kwargs
                                    )

                                except TypeError:
                                    return super(MockAttr, cls).__new__(cls)

                            def __call__(self, *args, **kwargs):
                                return v

                            def __bool__(self):
                                return bool(v)
                            __nonzero__ = __bool__

                        return MockAttr(v)

        return v

    def _patch(self, patches=None, **kwargs_patches):
        if not patches: patches = {}
        patches.update(kwargs_patches)
        for k, v in patches.items():
            if "." in k:
                k = k.split(".")[-1]
            setattr(self, k, v)

    def _raise_if_error(self, v):
        if self._is_instance(v, Exception):
            raise v
        elif self._is_subclass(v, Exception):
            raise v()

    def _is_instance(self, v, class_types):
        try:
            if isinstance(v, class_types):
                return True

        except TypeError:
            pass
        return False

    def _is_subclass(self, v, class_types):
        try:
            if issubclass(v, class_types):
                return True

        except TypeError:
            pass
        return False


###############################################################################
# testdata functions
###############################################################################
class MockData(TestData):
    def patch_instance(self, mod, patches=None, **kwargs_patches):
        """Helper function called from .patch() that will patch a class instance
        """
        if mod is None:
            raise ValueError("mod is empty")

        if not patches: patches = {}
        patches.update(kwargs_patches) # combine both dicts

        for name, patch in patches.items():
            val = getattr(mod, name, None)
            if inspect.isroutine(val):
                # we first try and patch as is, if we fail then we wrap the
                # patch in a lambda
                try:
                    setattr(mod, name, types.MethodType(patch, mod))

                except TypeError:
                    setattr(
                        mod,
                        name,
                        types.MethodType(
                            # lambda binding issue, see the explanation in
                            # patch_class why I'm using partial here
                            functools.partial(
                                lambda *a, **kw: kw["__patch"],
                                __patch=patch
                            ),
                            mod
                        )
                    )

            else:
                sentinel = name in mod.__class__.__dict__
                if sentinel:
                    sentinel = inspect.isdatadescriptor(
                        mod.__class__.__dict__[name]
                    )

                if sentinel:
                    # https://stackoverflow.com/a/30578922/5006
                    monkey_class = self.patch_class(
                        mod.__class__,
                        **{name: patch}
                    )
                    mod.__class__ = monkey_class

                else:
                    setattr(mod, name, patch)

        return mod

    def patch_class(self, mod, patches=None, **kwargs_patches):
        """Helper function called from .patch() that will patch a class type
        object"""
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

        class_name = '{}Patched'.format(mod.__name__)

        # http://stackoverflow.com/questions/9541025/how-to-copy-a-python-class
        mod_patched = type(
            class_name,
            tuple([mod] + list(mod.__bases__)),
            #{k: copy.deepcopy(v) for k, v in mod.__dict__.items()}
            copy_dict(mod)
        )
        for name, patch in patches.items():
            # make sure we have a callable if we need a callable
            o = getattr(mod_patched, name, None)
            if inspect.isroutine(o) and not inspect.isroutine(patch):
                # so I ran into an issue with binding here, the value of patch
                # was being changed on each iteration and so when I then called
                # it the final value of patch was being returned instead of the
                # value of patch when the lambda was created. a partial was the
                # only way I could figure out how to make it work and return the
                # correct value
                patch = functools.partial(
                    lambda *a, **kw: kw["__patch"],
                    __patch=patch
                )

            setattr(mod_patched, name, patch)

        return mod_patched

    def patch_module(self, mod, patches=None, **kwargs_patches):
        """Helper function called from .patch() that will patch a module"""
        if not mod:
            raise ValueError("mod is empty")

        if not patches: patches = {}
        patches.update(kwargs_patches) # combine both dicts

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
                    # we fudge the paths a bit to make sure current working
                    # directory is also checked
                    paths = [os.getcwd()]
                    paths.extend(sys.path)
                    spec = importlib.machinery.PathFinder().find_spec(p, paths)
                    if spec.submodule_search_locations:
                        mod_path = spec.submodule_search_locations[0]
                    else:
                        mod_path = spec.origin

                return mod_path

            mpath = find_mod_path(mod_name)

            mfile = mpath
            # figure out if we have a package or a module and set the
            # appropriate file
            if os.path.isdir(mpath):
                mfile = os.path.join(mpath, '__init__.py')

            else:
                if not mfile.endswith(".py"):
                    mfile = '{}.py'.format(mpath)

        mname = self.get_module_name(prefix=mod_name)
        #mname = '{}_{}'.format(mod_name, get_ascii(8))

        # ugh, this is deprecated in 3.4 (though it isn't throwing a warning
        m = importlib.machinery.SourceFileLoader(mname, mfile).load_module()
        # https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly

#         loader = importlib.machinery.SourceFileLoader(mname, mfile)
#         loaded = types.ModuleType(loader.name)
#         m = loader.exec_module(loaded)

        # go through and apply all the patches
        for patch_name, patch in patches.items():
            if "." in patch_name:
                parts = patch_name.split(".")
                sm = getattr(m, parts[0], None)
                if sm:
                    setattr(
                        m,
                        parts[0],
                        self.patch_module(
                            sm,
                            {".".join(parts[1:]): patch}
                        )
                    )
                else:
                    setattr(m, parts[0], Mock(**{parts[-1]: patch}))
            else:
                # if we're patching a function and patch isn't a function then
                # make it a function
                o = getattr(m, patch_name, None)
                if inspect.isroutine(o) and not inspect.isroutine(patch):
                    # lambda binding issue, see the explanation in patch_class
                    # why I'm using partial here
                    patch = functools.partial(
                        lambda *a, **kw: kw["__patch"], __patch=patch
                    )

                setattr(m, patch_name, patch)

        return m

    def patch(self, mod, patches=None, **kwargs_patches):
        """import module_name and apply the patches to it

        :param mod: string|module|class|instance, the name of the thing you are
            patching
        :param patches: dict, the keys are functions, classes, or modules that
            should be patched in the module, the value is the patched value you
            want to replace the key with
        :returns: module|object, if you pass in an object, return the object,
            otherwise return the module
        """
        if isinstance(mod, basestring):
            m = self.patch_module(mod, patches=patches, **kwargs_patches)

        elif inspect.ismodule(mod):
            m = self.patch_module(mod, patches=patches, **kwargs_patches)

        elif inspect.isclass(mod):
            m = self.patch_class(mod, patches=patches, **kwargs_patches)

        else:
            m = self.patch_instance(mod, patches=patches, **kwargs_patches) 

        return m

    def mock_class(self, name="", patches=None, **kwargs_patches):
        """create a class with the given method and properties

        :param name: string, the name of the class, default is just a random
            classname
        :param patches: dict, keys are attributes mapped to their values 
        :param **kwargs_patches: dict, keys will be attributes on the object
        :returns: type, the object
        """
        if not patches: patches = {}
        patches.update(kwargs_patches)
        return type(self.get_classname(name=name), (Mock,), patches)

    def mock_instance(self, name="", patches=None, **kwargs_patches):
        """This is the same as mock_class but returns an instance of that class

        see mock_class() docs"""
        return self.mock_class(name)(patches, **kwargs_patches)

    def mock(self, patches=None, **kwargs_patches):
        """Create a mocked object that tries to be really magical

        This is different than mock_instance because it creates an object that
        uses a lot
        of magic to try and be a jack of all trades

        :returns: Mock instance
        """
        return Mock(patches, **kwargs_patches)

    def mock_async(self, thing):
        """Wrap thing so any async calls will return their actual values

        :Example:
            class Foo(object):
                async bar(self, left, right):
                    return left + right


            instance = testdata.mock_async(Foo())
            print(instance.bar(1, 2)) # 3

            async def foo(left, right):
                return left + right

            afoo = testdata.mock_async(foo)
            print(afoo(1, 2)) # 3

        :param thing: callable|object|coroutine
        :returns Any|AsyncRunner instance
        """
        if asyncio.iscoroutine(thing):
            return AsyncRunner.normalize(thing)

        else:
            # if it has a __call__ and __func__ it's a method
            # if it has a __call__ and __name__ it's a function
            # if it just has a __call__ it's most likely an object instance
            d = dir(thing)
            if "__call__" in d and ("__func__" in d or "__name__" in d):
                return AsyncRunner.decorate(thing)

            else:
                return AsyncRunner(thing)

    @contextmanager
    def environment(self, thing=None, **kwargs):
        """Context manager to change the os.environ to something else for the
            life of the with statement

        :Example:
            with testdata.environ(FOO="bar"):
                print(os.environ["FOO"]) # bar

            print(os.environ["FOO"]) # keyError

        :param **kwargs: key is the environment variable name and value is the
            value
        """
        normalize_value = lambda v: v
        if thing is None:
            thing = os.environ
            normalize_value = lambda v: String(v)

        def has_key(thing, k):
            if isinstance(thing, Mapping):
                ret = k in thing
            else:
                ret = hasattr(thing, k)
            return ret

        def set_key(thing, k, v):
            if isinstance(thing, Mapping):
                thing[k] = v
            else:
                setattr(thing, k, v)

        def get_key(thing, k):
            if isinstance(thing, Mapping):
                ret = thing[k]
            else:
                ret = getattr(thing, k)
            return ret

        def del_key(thing, k):
            if isinstance(thing, Mapping):
                thing.pop(k)
            else:
                delattr(thing, k)

        originals = {}
        try:
            for k, v in kwargs.items():
                if has_key(thing, k):
                    originals[k] = get_key(thing, k)

                set_key(thing, k, normalize_value(v))

            yield originals

        finally:
            for k, v in kwargs.items():
                if k in originals:
                    set_key(thing, k, originals[k])
                else:
                    del_key(thing, k)
    modify = environment
    change = environment
    configure = environment
    environ = environment


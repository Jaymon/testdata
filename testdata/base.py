# -*- coding: utf-8 -*-
import functools
import inspect

from datatypes import (
    ReflectClass,
    ReflectModule,
    ReflectPath,
    ReflectCallable,
    OrderedSubclasses,
    Dirpath,
)
from datatypes import logging

from .compat import *
from .config import environ


# this module is really verbose so we're going to raise its default level to be
# a bit more quiet
logging.setdefault(__name__, "INFO")
logger = logging.getLogger(__name__)


class TestDatas(OrderedSubclasses):
    """Holds TestData children that are used for attribute resolution

    This is an internal class used by TestData and shouldn't be messed with
    unless you really know what you're doing
    """
    def __init__(self):
        super().__init__()
        self.clear()

    def default_cutoff(self):
        return (TestData,)

    def insert(self, data_class):
        """Add a TestData child

        :param data_class: TestData, the child class to add to the attribute
            resolution list
        """
        super().insert(data_class)
        self.data_instances[data_class] = data_class()

    def remove(self, data_class):
        """Removes data_class from the method resolution list, this means it
        will no longer be checked when resolving attributes

        :param data_class: the TestData child to remove
        """
        super().remove(data_class)
        self.data_instances.pop(data_class)

    def insert_module(self, modpath):
        rm = ReflectModule(modpath)
        for mod in rm.get_modules():
            self.module_prefixes.add(mod.__name__)

    def insert_modules(self):
        """Goes through the TESTDATA_PREFIX evnironment variables and loads any
        found module classpaths and loads all the classes found in those
        modules
        """
        if not self.inserted_modules:
            self.inserted_modules = True

            for modpath in environ.paths("PREFIX"):
                self.insert_module(modpath)

            # if there aren't any defined prefixes let's inspect the current
            # working directory
            if not self.module_prefixes:
                rp = ReflectPath(Dirpath.cwd())
                for mod in rp.find_modules("testdata"):
                    self.module_prefixes.add(mod.__name__)

    def items(self, **kwargs):
        """Iterate through all the TestData children that should be checked to
        resolve an attribute

        :returns: generator[str, TestData]
        """
        for data_name, data_class in super().items(**kwargs):
            try:
                yield data_name, self.data_instances[data_class]

            except KeyError:
                pass

    def clear(self):
        super().clear()

        self.data_instances = {}

        self.module_prefixes = set()
        self.inserted_modules = False


class TestData(object):
    """Any testdata sources should extend this class, this will register them
    with the testdata module without you having to do anything else

    :Example:
        from testdata import TestData

        class CustomData(TestData):
            def foobar(self):
                return "foobar"

            def get_int(self, *args, **kwargs):
                # overrides default get_int functionality
                return 1

        testdata.foobar() # foobar
        testdata.get_int() # 1


    This class, and all its children, have very complicated method resolution,
    with each child class able to call methods from every other class.

    A method of a subclass can call a method from another subclass using
    self.<NAME>. The secret to this working is .__getattr__ and .__findattr__

    Methods should be named globally unique across the entire set of child
    classes. If two child unrelated classes have a .get_foo() method the
    resolution is undefined

    To override methods, you should extend that specific child class, since
    the absolute child is the only TestData subclass that will be checked.
    """
    _data_instances = TestDatas()
    """Holds an active instance of each data class"""

    def __init__(self):
        # holds attributes that were requested but aren't available on this
        # instance. Since attribute resultion for these classes are so crazy
        # and very recursive, this keeping track of non-existent attributes on
        # the various TestData subclasses just speeds everything up
        self._missing_cache = set()

    @classmethod
    def add_class(cls, data_class):
        """Add a TestData child to the resolution list, this should mainly only
        be called from the TestData class itself

        :param data_class: TestData
        """
        cls._data_instances.insert(data_class)

    @classmethod
    def delete_class(cls, data_class):
        """Remove a TestData child to the resolution list, this should mainly
        only be called from the TestData class itself

        :param data_class: TestData
        """
        try:
            cls._data_instances.remove(data_class)

        except ValueError:
            pass

    @classmethod
    def __findattr__(cls, name):
        """Certain places (like the module testdata.__getattr__ and
        testdata.test.TestCase.__getattr__ use this method to find requested
        testdata methods

        .. note:: this method is actually quite recursive, basically, it will
        go through each data instance and try to get `name`, but if the data
        instance doesn't have the `name` attribute that will trigger that data
        instance to check all the data instances. Basically, it's turtles all
        the way down until all the `._missing_cache` variables are filled and
        things start returning

        :param name: str, the method/attribute name to check all the subclasses
            for
        :returns: Any, this will return a partial wrapped .__runattr__ method
            if testcase is not None
        """
        logger.debug("{}.__findattr__ looking for {}".format(
            cls.__name__,
            name,
        ))

        # we do this here so all of the magical loading coding is confined
        # to this class and also because trying to do this in __init__ can
        # easily cause circular imports and other bad things because the
        # instances aren't fully initialized. Basically, I'm telling future me
        # not to try and move this like present me tried to do
        if environ.AUTOLOAD and not cls._data_instances.inserted_modules:
            cls._data_instances.insert_modules()

        # go through all the absolute children classes and see if they have an
        # attribute that matches name
        for data_name, data_instance in cls._data_instances.items(edges=True):
            if name not in data_instance._missing_cache:

                logger.debug("{}.__findattr__ checking {}.{}".format(
                    cls.__name__,
                    data_name,
                    name
                ))

                try:
                    attribute = getattr(data_instance, name)

                    logger.debug("{}.__findattr__ found {}.{}".format(
                        cls.__name__,
                        data_name,
                        name
                    ))

                except AttributeError:
                    pass

                else:
                    return attribute

        # since we couldn't find an attribute in any of the classes, let's try
        # and see if there is an actual class that matches the name, then
        # return the class, this makes it easy to get a specific class
        for data_name, data_instance in cls._data_instances.items():
            if name == data_instance.__class__.__name__:
                logger.debug("{}.__findattr__ found data class {}".format(
                    cls.__name__,
                    name
                ))
                return data_instance

        # hail mary
        if not cls._data_instances.inserted_modules:
            cls._data_instances.insert_modules()
            if cls._data_instances.module_prefixes:
                return cls.__findattr__(name)

        raise AttributeError(name)

    @classmethod
    async def call_method(self, method_name, *args, **kwargs):
        """call `method_name` passing in `*args` and `**kwargs`

        This is just a convenience method for when you have a method's name
        as a string and you want to call it

        I almost called this `__callattr__` to match `.__findattr__`

        .. note:: this method has to be async so it can safely handle async
        testdata methods

        .. note:: `args` and `**kwargs` will be filtered and unknown arguments
        that the method doesn't accept will be filtered out before the method
        is called

        :param method_name: str, the method to call, this uses `.__findattr__`
            to find the actual method to call
        :argument *args: filtered and passed through to the actual method
            being called
        :keyword **kwargs: filtered and passed through to the actual method
            being called
        :returns: Any, whatever the method's return value is
        """
        cb = TestData.__findattr__(method_name)
        bind_info = ReflectCallable(cb).get_bind_info(*args, **kwargs)
        ret = cb(
            *bind_info["bound_args"],
            **bind_info["bound_kwargs"],
        )
        while inspect.iscoroutine(ret):
            ret = await ret

        return ret

    @classmethod
    def get_jsonable_value(self, value):
        """Does its very very best to convert `value` to something that can
        be serialized to json

        :param value: Any, the value that wants to be serialized to json
        :returns: Any, this value should hopefully be safe to encode to json
        """
        if isinstance(value, (basestring, float, int, bool)):
            ret = value

        elif isinstance(value, Mapping):
            ret = value

        elif isinstance(value, Sequence):
            ret = []
            for o in value:
                try:
                    ret.append(cls._get_object_json(o))

                except ValueError:
                    ret.append(o)

        elif isinstance(value, object):
            ret = cls._get_object_json(value)

        else:
            ret = value

        return ret

    @classmethod
    def _get_object_json(cls, o):
        """If the testdata method that was ran returns an object then this will
        try and figure out how to turn that object into json

        :param o: object, the generic object whose json value couldn't be
            inferred
        :returns: dict
        """
        # https://stackoverflow.com/a/51055044
        if hasattr(o, "jsonable"):
            ret = o.jsonable()

        elif hasattr(o, "to_json"):
            ret = o.to_json()

        elif hasattr(o, "toJSON"):
            ret = o.toJSON()

        elif hasattr(o, "tojson"):
            ret = o.tojson()

        elif hasattr(o, "json"):
            ret = o.json()

        elif hasattr(o, "__json__"):
            ret = o.__json__()

        else:
            ret = String(o)

        return ret

    def __init_subclass__(cls, *args, **kwargs):
        """This is where all the magic happens, when a class is read into
        memory this method will be called

        https://peps.python.org/pep-0487/

        NOTE -- This will automatically add the class to the method resolution
        list unless the class's name begins with an underscore, because a class
        that begins with an underscore is considered private and shouldn't be
        automatically used. It could still be added by calling .add_class
        manually though
        """
        super().__init_subclass__(*args, **kwargs)

        if cls.__name__.startswith("_"):
            logger.debug(" ".join([
                "Not automatically adding {} to method resolution".format(
                    cls.__name__
                ),
                "because it begins with an underscore"
            ]))

        else:
            cls.add_class(cls)

    def __getattr__(self, name):
        """This allows child classes to reference any other registered class's
        methods

        if we get to this __getattr__ then this object doesn't have the
        attribute, so we keep track of name so we won't have to check this
        instance again.

        We don't passthrough anything that begins with a double underscore.

        :param name: str, the requested attribute name
        """
        # see __findattr__ to see where self._missing_cache is checked
        self._missing_cache.add(name)

        if name.startswith("_"):
            return super().__getattr__(name)

        else:
            # magic resolution is only supported for non magic/private
            # attributes
            return self.__findattr__(name)


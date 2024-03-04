# -*- coding: utf-8 -*-
import functools

from datatypes import (
    ReflectClass,
    ReflectModule,
    OrderedSubclasses,
)
from datatypes import logging


# this module is really verbose so we're going to raise its default level to be
# a bit more quiet
logging.setdefault(__name__, "INFO")
logger = logging.getLogger(__name__)


class DataInstances(object):
    """Holds TestData children that are used for attribute resolution

    This is an internal class used by TestData and shouldn't be messed with
    unless you really know what you're doing
    """
    def __init__(self):
        self.data_classes = OrderedSubclasses()
        self.data_instances = {}

    def add(self, data_class):
        """Add a TestData child

        :param data_class: TestData, the child class to add to the attribute
            resolution list
        """
        self.data_classes.insert(data_class, (TestData,))
        self.data_instances[data_class] = data_class()

    def delete(self, data_class):
        """Removes data_class from the method resolution list, this means it
        will no longer be checked when resolving attributes

        :param data_class: the TestData child to remove
        """
        self.data_classes.remove(data_class)
        self.data_instances.pop(data_class)

    def edges(self):
        """Iterate through all the TestData children that should be checked to
        resolve an attribute

        :returns: generator[str, TestData]
        """
        for data_name, data_class in self.data_classes.items(edges=True):
            yield data_name, self.data_instances[data_class]

    def items(self):
        for data_name, data_class in self.data_classes.items():
            if data_class is not object:
                try:
                    yield data_name, self.data_instances[data_class]

                except KeyError:
                    pass


class TestData(object):
# class TestData(_BaseTestData, metaclass=_TestDataMeta):
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
    _data_instances = DataInstances()
    """Holds an active instance of each data class"""

    def __init__(self):
        # holds attributes that were requested but aren't available on this
        # instance. Since attribute resultion for these classes are so crazy and
        # very recursive, this keeping track of non-existent attributes on the
        # various TestData subclasses just speeds everything up
        self._missing_cache = set()

    @classmethod
    def add_class(cls, data_class):
        """Add a TestData child to the resolution list, this should mainly only
        be called from the TestData class itself

        :param data_class: TestData
        """
        cls._data_instances.add(data_class)

    @classmethod
    def delete_class(cls, data_class):
        """Remove a TestData child to the resolution list, this should mainly
        only be called from the TestData class itself

        :param data_class: TestData
        """
        cls._data_instances.delete(data_class)

    @classmethod
    def __findattr__(cls, name):
        """Certain places (like the module testdata.__getattr__ and
        testdata.test.TestCase.__getattr__ use this method to find requested
        testdata methods

        NOTE -- this method is actually quite recursive, basically, it will
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

        # go through all the absolute children classes and see if they have an
        # attribute that matches name
        for data_name, data_instance in cls._data_instances.edges():
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
        # and see if there is an actual class that matches the name, then return
        # the class, this makes it easy to get a specific class
        for data_name, data_instance in cls._data_instances.items():
            if name == data_instance.__class__.__name__:
                logger.debug("{}.__findattr__ found data class {}".format(
                    cls.__name__,
                    name
                ))
                return data_instance

        raise AttributeError(name)

    def __init_subclass__(cls, *args, **kwargs):
        """This is where all the magic happens, when a class is read into memory
        this method will be called

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


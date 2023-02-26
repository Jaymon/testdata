# -*- coding: utf-8 -*-
import functools
import logging

from datatypes import (
    ReflectClass,
    ReflectModule,
)


logger = logging.getLogger(__name__)


class TestData(object):
    """Any testdata sources should extend this class, this will register them with
    the testdata module without you having to do anything else

    :Example:
        from testdata.base import TestData

        class CustomData(TestData):
            def foobar(self):
                return "foobar"

            def get_int(self, *args, **kwargs):
                # overrides default get_int functionality
                return 1

        testdata.foobar() # foobar
        tetdata.get_int() # 1
    """
    _data_instances = {}
    """Holds an active instance of each data class"""

    def __init__(self):
        # holds attributes that were requested but aren't available on this instance
        self._missing_cache = set()

    @classmethod
    @functools.cache
    def module(cls):
        """Get the testdata module"""
        return ReflectModule(__name__).basemodule()

    @classmethod
    def __findattr__(cls, name):
        """Certain places (like the module testdata.__getattr__ and
        testdata.test.TestCase.__getattr__ use this method to find requested testdata
        methods

        :param name: str, the method/attribute name to check all the subclasses
            for
        :returns: mixed
        """
        for data_instance in cls._data_instances.values():
            if name not in data_instance._missing_cache:
                try:
                    return getattr(data_instance, name)

                except AttributeError:
                    pass

        raise AttributeError(name)

    def __init_subclass__(cls, *args, **kwargs):
        """This is where all the magic happens, when a class is read into memory
        this method will be called

        https://peps.python.org/pep-0487/
        """
        super().__init_subclass__(*args, **kwargs)

        module = cls.module()

        data_instance = cls()

        rc = ReflectClass(cls)
        cls._data_instances[rc.classpath] = data_instance

        # clear any parents since this class will supercede them
        for rp in rc.reflect_parents(TestData):
            cls._data_instances.pop(rp.classpath, None)

    def __getattr__(self, name):
        """This allows child classes to reference any other registered class's
        methods

        if we get to this __getattr__ then this object doesn't have the attribute,
        but to allow instances to reference TestData methods found in other instances
        we need to passthrough to the other instances, but we keep track of name
        so we won't have to check this instance again

        :param name: str, the requested attribute name. This will only ever be
            requested once if it makes it this far, see __getattr_subclass__ to
            see where self._missing_cache is checked
        """
        self._missing_cache.add(name)
        return self.__findattr__(name)


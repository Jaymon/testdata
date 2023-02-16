# -*- coding: utf-8 -*-
import functools
import inspect

from datatypes import (
    ReflectClass,
    ReflectModule,
)


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
    data_instances = {}
    """Holds an active instance of each data class"""

    @classmethod
    @functools.cache
    def module(cls):
        """Get the testdata module"""
        return ReflectModule(__name__).basemodule()

    @classmethod
    def register(cls, data_class):
        """Register a data_class

        when a new class is registered, it's public methods (any method that doesn't
        begin with an underscore) will be registered to cls.module(). Last class
        wins, that means if you have a data class that defines .foobar() and then
        later on another class is registered that defines .foobar(), the later
        class's .foobar() method will be used

        :param data_class: class, a class that extends TestData
        """
        instance = data_class()

        reclass = ReflectClass(cls)
        for rc in reclass.reflect_classes(TestData):
            cls.data_instances[rc.classpath] = instance

        module = cls.module()
        for method_name, method in inspect.getmembers(instance, inspect.ismethod):
            if not method_name.startswith("_"):
                setattr(module, method_name, method)

    def __init_subclass__(cls, *args, **kwargs):
        """This is where all the magic happens, when a class is read into memory
        this method will be called

        https://peps.python.org/pep-0487/
        """
        super().__init_subclass__(*args, **kwargs)
        cls.register(cls)

    def __getattr__(self, name):
        """This allows child classes to reference any other registered class's
        methods"""
        if name.startswith("_"):
            return super().__getattr__(name)

        else:
            return getattr(self.module(), name)


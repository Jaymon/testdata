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
        # holds attributes that were requested but aren't available on this
        # instance. Since attribute resultion for these classes are so crazy and
        # very recursive, this keeping track of non-existent attributes on the
        # various TestData subclasses just speeds everything up
        self._missing_cache = set()

        # holds the current TestCase class that is running. This should never
        # be messed with outside of .__findattr__, check out .__runattr__ and 
        # __getattribute__ to also to see how this is used in practice
        self._testcase = None

#     @classmethod
#     @functools.cache
#     def module(cls):
#         """Get the testdata module"""
#         return ReflectModule(__name__).basemodule()

    @classmethod
    def __findattr__(cls, name, testcase=None):
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
        :param testcase: TestCase, this can be an instance or class/type, it
            will be set into ._testcase for each data instance looked at and
            then cleared when that data instance is done being checked
        :returns: mixed
        """
        logger.debug("{}.__findattr__ looking for {} with {}".format(
            cls.__name__,
            name,
            "testcase" if testcase else "no testcase"
        ))

        for data_name, data_instance in cls._data_instances.items():

#             pout.v(data_name, data_instance._missing_cache, id(data_instance))

#             if name == "get_foo":
#                 pout.v(data_instance.__class__.__name__)

#             if name not in data_instance._missing_cache:
            if name not in data_instance._missing_cache:
                data_instance._testcase = testcase

                logger.debug("{}.__findattr__ checking {} for {}".format(
                    cls.__name__,
                    data_name,
                    name
                ))

                try:
                    attribute = getattr(data_instance, name)

                    logger.debug("{}.__findattr__ found {} in {}".format(
                        cls.__name__,
                        name,
                        data_name
                    ))


                except AttributeError:
                    data_instance._missing_cache.add(name)

                else:
                    if testcase and callable(attribute):
                        return functools.partial(
                            data_instance.__runattr__,
                            attribute,
                            testcase
                        )

#                         def testcase_resolve(*args, **kwargs):
#                             pout.v(attribute, data_instance)
#                             data_instance._testcase = testcase
#                             try:
#                                 return attribute(*args, **kwargs)
# 
#                             finally:
#                                 data_instance._testcase = None
# 
#                         return testcase_resolve

                    else:
                        return attribute

                finally:
                    data_instance._testcase = None

        raise AttributeError(name)

    def __runattr__(self, callback, testcase, *args, **kwargs):
        self._testcase = testcase
        try:
            return callback(*args, **kwargs)

        finally:
            self._testcase = None

    def __init_subclass__(cls, *args, **kwargs):
        """This is where all the magic happens, when a class is read into memory
        this method will be called

        https://peps.python.org/pep-0487/
        """
        super().__init_subclass__(*args, **kwargs)

        data_instance = cls()
        rc = ReflectClass(cls)

        cls._data_instances[rc.classpath] = data_instance

        # clear any parents since this class will supercede them
        for rp in rc.reflect_parents(TestData):
            cls._data_instances.pop(rp.classpath, None)

    def __getattr__(self, name):
        """This allows child classes to reference any other registered class's
        methods

        if we get to this __getattr__ then this object doesn't have the
        attribute, but to allow instances to reference TestData methods found
        in other instances we need to passthrough to the other instances, but
        we keep track of name so we won't have to check this instance again

        :param name: str, the requested attribute name. This will only ever be
            requested once if it makes it this far, see __findattr__ to
            see where self._missing_cache is checked
        """
        self._missing_cache.add(name)

        if name.startswith("__"):
            return super().__getattr__(name)

        else:
            # magic resolution is only supported for non magic/private
            # attributes
            return self.__findattr__(name, testcase=self._testcase)

    def __getattribute__(self, name):
        if name == "_testcase" or name.startswith("__"):
            return super().__getattribute__(name)

        else:
            try:
                testcase = super().__getattribute__("_testcase")

            except AttributeError:
                testcase = None

            finally:
                if testcase:
                    methods = dir(testcase)
                    if name in methods:
                        return getattr(testcase, name)

        return super().__getattribute__(name)


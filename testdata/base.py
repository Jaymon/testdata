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
        # instance
        self._missing_cache = set()

        # holds the current TestCase class that is running
        self.testcase = None

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
            will be set into .testcase for each data instance looked at and then
            cleared when that data instance is done being checked
        :returns: mixed
        """
        logger.debug("{}.__findattr__ looking for {} with testcase {}".format(
            cls.__name__,
            name,
            True if testcase else False
        ))

        for data_name, data_instance in cls._data_instances.items():

#             if name == "get_foo":
#                 pout.v(data_instance.__class__.__name__)

#             if name not in data_instance._missing_cache:
            if name in data_instance._missing_cache:
                logger.debug("{}.__findattr__ ignoring {} for {}".format(
                    cls.__name__,
                    data_name,
                    name
                ))

            else:
                logger.debug("{}.__findattr__ checking {} for {}".format(
                    cls.__name__,
                    data_name,
                    name
                ))

                data_instance.testcase = testcase
                try:
#                     r = getattr(data_instance, name)
#                     if name == "get_foo":
#                         pout.v(data_instance.__class__.__name__)
#                         pout.v(testcase)
#                         pout.v(cls)
#                         pout.v(r)
#                         return r

                    r = getattr(data_instance, name)

                    logger.debug("{}.__findattr__ found {} in {}".format(
                        cls.__name__,
                        name,
                        data_name
                    ))

                    return r

                except AttributeError:
                    data_instance._missing_cache.add(name)

                except Exception as e:
                    pout.v(e)
                    raise

                finally:
                    data_instance.testcase = None

                    logger.debug("{} clearing testcase".format(
                        data_name
                    ))

        raise AttributeError(name)

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
        return self.__findattr__(name, testcase=self.testcase)

#     def __getattribute__(self, name):
#         if not name.startswith("_"):
#             try:
#                 testcase = super().__getattribute__("testcase")
# 
#             except AttributeError:
#                 pass
# 
# #             else:
# #                 pout.v(name)
# #                 pout.v(testcase.__class__.__name__)
# #                 tcd = set(dir(testcase))
# #                 if name in tcd:
# #                     pout.v(name)
# #                     return getattr(testcase, name)
# 
#         return super().__getattribute__(name)


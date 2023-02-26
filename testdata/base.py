# -*- coding: utf-8 -*-
import functools
import inspect
import logging

from datatypes import (
    ReflectClass,
    ReflectModule,
    OrderedSubclasses,
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
    data_instances = {}
    """Holds an active instance of each data class"""

    __getting_attr__ = 0

    def __init__(self):
        self._missing_cache = set()



    @classmethod
    @functools.cache
    def module(cls):
        """Get the testdata module"""
        return ReflectModule(__name__).basemodule()


    @classmethod
    def __getattr_subclasses__(cls, name):
        #logger.debug(f"Checking all TestData classes for {name}")
        for data_instance in cls.data_instances.values():
            if name not in data_instance._missing_cache:
                try:
                    return getattr(data_instance, name)

                except AttributeError:
                    pass

        #logger.debug(f"TestData classes do not have attribute {name}")
        raise AttributeError(name)



#     @classmethod
#     def __getattr_subclasses__(cls, name):
#         #logger.debug(f"Checking all TestData classes for {name}")
#         for data_instance in cls.data_instances.values():
#             #if data_instance.__class__ is not cls:
#             #logger.debug(f"{cls.__name__} checking for {data_instance.__class__.__name__}.{name} ({data_instance.__getting_attr__})")
#             #pout.v(f"Checking {data_instance.__class__.__name__} ({data_instance.__getting_attr__})")
#             try:
#                 return getattr(data_instance, name)
# 
#             except AttributeError:
#                 pass
# 
#         #logger.debug(f"TestData classes do not have attribute {name}")
#         raise AttributeError(name)

    @classmethod
    def __update_subclasses__(cls):
        for data_instance in cls.data_instances.values():
            data_instance._update()

    @classmethod
    def __insert_subclass__(cls, data_class):
        """Register a data_class

        when a new class is registered, it's public methods (any method that doesn't
        begin with an underscore) will be registered to cls.module(). Last class
        wins, that means if you have a data class that defines .foobar() and then
        later on another class is registered that defines .foobar(), the later
        class's .foobar() method will be used

        :param data_class: class, a class that extends TestData
        """
        module = cls.module()

        data_instance = data_class()

        rc = ReflectClass(cls)
        cls.data_instances[rc.classpath] = data_instance

        # clear any parents since this class will supercede them
        for rp in rc.reflect_parents(TestData):
            cls.data_instances.pop(rp.classpath, None)

        data_instance._insert()

    def __init_subclass__(cls, *args, **kwargs):
        """This is where all the magic happens, when a class is read into memory
        this method will be called

        https://peps.python.org/pep-0487/
        """
        super().__init_subclass__(*args, **kwargs)
        cls.__insert_subclass__(cls)

    def _insert(self):
        pass

    def _update(self):
        pass

    def __getattr__(self, name):
        self._missing_cache.add(name)
        return self.__getattr_subclasses__(name)




#         if name in self._missing_cache:
#             raise AttributeError(name)
# 
#         else:
#             self._missing_cache.add(name)
#             return self.__getattr_subclasses__(name)



#     def __getattr__(self, name):
#         """This allows child classes to reference any other registered class's
#         methods"""
# 
#         #pout.v(f"{self.__class__.__name__}.{name} ({self.__getting_attr__})")
# 
#         if self.__getting_attr__ > 0:
#             #logger.debug(f"{self.__class__.__name__}.__getting_attr__ = {self.__getting_attr__}")
#             raise AttributeError(f"{self.__class__.__name__} is already checking for {name}")
# 
#         else:
#             # if we get to here then this object doesn't have the attribute
#             self.__getting_attr__ += 1
# 
#             try:
#                 return self.__getattr_subclasses__(name)
# 
#             finally:
#                 self.__getting_attr__ -= 1
# 
#             # if we get to here then this object doesn't have the attribute
# #             for di in self.data_instances.values():
# #                 if self is not di:
# #                     try:
# #                         ret = getattr(di, name)
# # 
# #                     except AttributeError:
# #                         pass
# # 
# #                     else:
# #                         self.__getting_attr = False
# #                         return ret
# 
#         #raise AttributeError(name)
# 

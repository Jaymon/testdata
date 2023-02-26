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
#     data_classes = OrderedSubclasses()

    data_instances = {}
    """Holds an active instance of each data class"""

#     register_methods = []
#     has_registered = False

    @classmethod
    @functools.cache
    def module(cls):
        """Get the testdata module"""
        return ReflectModule(__name__).basemodule()

    @classmethod
    def __getattr_subclasses__(cls, name):
        for data_instance in cls.data_instances.values():
            try:
                return getattr(data_instance, name)

            except AttributeError:
                pass

        raise AttributeError(name)



#         module = cls.module()
#         for data_instance in cls.data_instances.values():
#             try:
#                 attr = getattr(data_instance, k)
#                 # let's cache this in the testdata module
#                 setattr(module, k, attr)
#                 return attr
# 
#             except AttributeError:
#                 pass
# 
#         raise AttributeError(k)

    @classmethod
    def __update_subclasses__(cls):
        module = cls.module()
        for data_instance in cls.data_instances.values():
            data_instance._inject_update(module)

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
#         if not cls.data_classes:
#             cls.data_classes = OrderedSubclasses(TestData)

#         instance = data_class()
#         cls.data_classes.append(data_class)

        module = cls.module()
        data_instance = data_class()

#         reclass = ReflectClass(cls)
#         for rc in reclass.reflect_classes(TestData):
#             cls.data_instances[rc.classpath] = instance
        rc = ReflectClass(cls)
        cls.data_instances[rc.classpath] = data_instance

        # clear any parents since this class will supercede them
        for rp in rc.reflect_parents(TestData):
            cls.data_instances.pop(rp.classpath, None)

        data_instance._inject_insert(module)

#         cls.data_instances[reclass.classpath] = instance

#         classpath = rc.classpath
#         if classpath not in cls.data_instances:
#             instance = data_class()
#             cls.data_instances[classpath] = instance
#             instance.inject_into(module)







#         reclass = ReflectClass(cls)
#         for rc in reclass.reflect_classes(TestData):
#             cls.data_instances[rc.classpath] = instance
# 
#         module = cls.module()
#         for method_name, method in inspect.getmembers(instance, inspect.ismethod):
#             if method_name == "register":
#                 cls.register_methods.append(method)
# 
#             if not method_name.startswith("_"):
#                 setattr(module, method_name, method)

#     @classmethod
#     def inject(cls):
#         module = cls.module()
# 
#         for data_class in cls.data_classes.edges():
#             reclass = ReflectClass(cls)
#             classpath = rc.classpath
#             if classpath not in cls.data_instances:
#                 instance = data_class()
#                 cls.data_instances[classpath] = instance
#                 instance.inject_into(module)


#         module = cls.module()
#         for method_name, method in inspect.getmembers(instance, inspect.ismethod):
#             if method_name == "register":
#                 cls.register_methods.append(method)
# 
#             if not method_name.startswith("_"):
#                 setattr(module, method_name, method)



#     @classmethod
#     def register_module(cls):
#         if not cls.has_registered:
#             for register_method in cls.register_methods:
#                 logger.debug(f"Registering TestData class with {register_method.__qualname__}")
#                 register_method()
# 
#             cls.has_registered = True

    def __init_subclass__(cls, *args, **kwargs):
        """This is where all the magic happens, when a class is read into memory
        this method will be called

        https://peps.python.org/pep-0487/
        """
        #pout.v(cls.__name__)
        super().__init_subclass__(*args, **kwargs)
        cls.__insert_subclass__(cls)

    def _inject_insert(self, module):
        return

        ignore_methods = set(["module"])
#         ignore_methods = set(["inject_into", "inject_insert", "inject_update", "module"])
        for method_name, method in inspect.getmembers(self, inspect.ismethod):
            if not method_name.startswith("_") and method_name not in ignore_methods:
                setattr(module, method_name, method)

        # update should be guarranteed to be called at least once during
        # execution, this will allow child classes to run their update code even
        # if they don't use testdata.test.TestCase that calls
        # __update_subclass__
        self._inject_update(module)

    def _inject_update(self, module):
        pass

#     def register(self):
#         module = cls.module()
#         for method_name, method in inspect.getmembers(instance, inspect.ismethod):
#             if method_name == "register":
#                 cls.register_methods.append(method)
# 
#             if not method_name.startswith("_"):
#                 setattr(module, method_name, method)


    def __getattr__(self, name):
        """This allows child classes to reference any other registered class's
        methods"""
        for data_instance in self.data_instances.values():
            data_class = type(data_instance)
            if name in data_class.__dict__:
                return getattr(data_instance, name)

        raise AttributeError(name)




#         if name.startswith("_"):
#             return super().__getattr__(name)
# 
#         else:
#             for data_instance in self.data_instances.values():
#                 if not (self is data_instance):
#                     try:
#                         return getattr(data_instance, name)
#                         # let's cache this in the testdata module
#                         #setattr(module, k, attr)
#                         #return attr
# 
#                     except AttributeError:
#                         pass
# 
#             raise AttributeError(name)

            #return getattr(self.module(), name)


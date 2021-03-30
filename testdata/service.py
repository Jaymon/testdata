# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from datatypes.service import Service


###############################################################################
# Supporting classes and methods
###############################################################################


###############################################################################
# testdata functions
###############################################################################

def start_service(service_name, ignore_failure=True):
    """start a local service

    :param service_name: string, the service you want to start
    :param ignore_failure: bool, True if it should ignore a failure return code
    :returns: Service instance
    """
    s = Service(service_name, ignore_failure)
    s.start()
    return s


def stop_service(service_name, ignore_failure=True):
    """stop a local service

    :param service_name: string, the service you want to stop
    :param ignore_failure: bool, True if it should ignore a failure return code
    :returns: Service instance
    """
    s = Service(service_name, ignore_failure)
    s.stop()
    return s


def restart_service(service_name, ignore_failure=True):
    """see start_service() and stop_service()"""
    stop_service(service_name, ignore_failure)
    return start_service(service_name, ignore_failure)



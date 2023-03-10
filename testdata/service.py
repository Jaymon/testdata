# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from datatypes.service import Service

from .base import TestData


###############################################################################
# testdata functions
###############################################################################
class ServiceData(TestData):
    def start_service(self, service_name, ignore_failure=True):
        """start a local service

        :param service_name: string, the service you want to start
        :param ignore_failure: bool, True if it should ignore a failure return code
        :returns: Service instance
        """
        s = Service(service_name, ignore_failure)
        s.start()
        return s

    def stop_service(self, service_name, ignore_failure=True):
        """stop a local service

        :param service_name: string, the service you want to stop
        :param ignore_failure: bool, True if it should ignore a failure return code
        :returns: Service instance
        """
        s = Service(service_name, ignore_failure)
        s.stop()
        return s

    def restart_service(self, service_name, ignore_failure=True, **kwargs):
        """see start_service() and stop_service()

        :param service_name: string, the service you want to restart (stop then start)
        :param ignore_failure: bool, True if it should ignore a failure return code,
            if a specific ignore_*_failure flag is not passed in then this will be
            used instead
        :param **kwargs:
            ignore_stop_failure: takes precedence over ignore_failure, only ignores
                failures while stopping the service
            ignore_start_failure: takes precedence over ignore_failure, only ignores
                failures while starting the service
        :returns: Service instance
        """
        self.stop_service(
            service_name,
            kwargs.get("ignore_stop_failure", ignore_failure)
        )
        return self.start_service(
            service_name,
            kwargs.get("ignore_start_failure", ignore_failure)
        )


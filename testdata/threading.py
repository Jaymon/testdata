# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import threading
import sys
import logging

from .compat import queue, thread, reraise


logger = logging.getLogger(__name__)
exc_queue = queue.Queue()


# def monitor_errors():
#     # this doesn't work because in the end it would be in a thread when it reraises
#     # the error, so this isn't any better than what Thread already does
#     global exc_queue
#     thread_e_info = None
#     pout.h()
#     try:
#         thread_e_info = exc_queue.get(False)
#     except queue.Empty:
#         pass
# 
#     finally:
#         pout.h()
#         #exc_queue.task_done()
#         if thread_e_info:
#             pout.h()
#             thread_e, thread_exc_info = thread_e_info
#             reraise(*thread_exc_info)
# 
#         else:
#             pout.h()
#             t = threading.Timer(0.1, monitor_errors)
#             t.daemon = True
#             t.start()


class Thread(threading.Thread):
    """
    Drop in replacement for the standard Thread that raises any error

    by default, the threading library suppresses exceptions, this makes using a thread
    for testing kind of annoying since AssertionErrors don't get picked up correctly, but
    this thread will throw the error if .join() is used, and raise a KeyboardInterrupt if
    .join() isn't used (stopping on the error is better than nothing)
    """
    @property
    def exception(self):
        """this will hold the exception if KeyboardInterrupt is raised and .join()
        isn't used"""
        global exc_queue
        #exc_queue = self.queue
        thread_e_info = None
        try:
            thread_e_info = exc_queue.get(False)
            exc_queue.task_done()

        except queue.Empty:
            pass

        return thread_e_info[0] if thread_e_info else None


#     def __init__(self, **kwargs):
#         #self.queue = queue.Queue()
#         super(Thread, self).__init__(**kwargs)

    def run(self, *args, **kwargs):
        try:
            super(Thread, self).run(*args, **kwargs)

        except Exception as e:
            # http://stackoverflow.com/a/1854263/5006
            global exc_queue
            #exc_queue = self.queue
            exc_info = sys.exc_info()
            exc_queue.put((e, exc_info))
            logger.exception(e)
            thread.interrupt_main()

    def join(self, *args, **kwargs):
        try:
            super(Thread, self).join(*args, **kwargs)

        except KeyboardInterrupt as e:
            pass

        finally:
            global exc_queue
            #exc_queue = self.queue
            thread_e_info = None
            try:
                thread_e_info = exc_queue.get(False)
                exc_queue.task_done()

            except queue.Empty:
                pass

            finally:
                if thread_e_info:
                    thread_e, thread_exc_info = thread_e_info
                    reraise(*thread_exc_info)


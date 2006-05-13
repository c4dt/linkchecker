# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006 Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""
Management of checking a queue of links with several threads.
"""

import os
import sys
import codecs
import traceback
import time
import linkcheck.i18n
import linkcheck.cache.urlqueue
import linkcheck.cache.robots_txt
import linkcheck.cache.cookie
import linkcheck.cache.connection
import aggregator


_encoding = linkcheck.i18n.default_encoding
stderr = codecs.getwriter(_encoding)(sys.stderr, errors="ignore")


def internal_error ():
    """
    Print internal error message to stderr.
    """
    print >> stderr, os.linesep
    print >> stderr, _("""********** Oops, I did it again. *************

You have found an internal error in LinkChecker. Please write a bug report
at http://sourceforge.net/tracker/?func=add&group_id=1913&atid=101913
or send mail to %s and include the following information:
- the URL or file you are testing
- your commandline arguments and/or configuration.
- the output of a debug run with option "-Dall" of the executed command
- the system information below.

Disclosing some of the information above due to privacy reasons is ok.
I will try to help you nonetheless, but you have to give me something
I can work with ;) .
""") % linkcheck.configuration.Email
    etype, value = sys.exc_info()[:2]
    print >> stderr, etype, value
    traceback.print_exc()
    print_app_info()
    print >> stderr, os.linesep, \
            _("******** LinkChecker internal error, over and out ********")
    sys.exit(1)


def print_app_info ():
    """
    Print system and application info to stderr.
    """
    print >> stderr, _("System info:")
    print >> stderr, linkcheck.configuration.App
    print >> stderr, _("Python %s on %s") % (sys.version, sys.platform)
    for key in ("LC_ALL", "LC_MESSAGES",  "http_proxy", "ftp_proxy"):
        value = os.getenv(key)
        if value is not None:
            print >> stderr, key, "=", repr(value)


def check_urls (aggregate):
    """
    Main check function; checks all configured URLs until interrupted
    with Ctrl-C.
    @return: None
    """
    try:
        aggregate.logger.start_log_output()
        if not aggregate.urlqueue.empty():
            aggregate.start_threads()
        # blocks until all urls are checked
        aggregate.urlqueue.join()
        aggregate.logger.end_log_output()
    except (KeyboardInterrupt, SystemExit):
        aggregate.abort()
    except:
        aggregate.abort()
        internal_error()


def print_status (urlqueue, start_time):
    duration = time.time() - start_time
    tocheck, tasks, links = urlqueue.status()
    msg = _n("%5d URL queued,", "%5d URLs queued,", tocheck) % tocheck
    print >> stderr, msg,
    msg = _n("%4d URL checked,", "%4d URLs checked,", links) % links
    print >> stderr, msg,
    msg = _n("%2d active task,", "%2d active tasks,", tasks) % tasks
    print >> stderr, msg,
    msg = _("runtime %s") % linkcheck.strformat.strduration_long(duration)
    print >> stderr, msg


def get_aggregate (config):
    urlqueue = linkcheck.cache.urlqueue.UrlQueue()
    connections = linkcheck.cache.connection.ConnectionPool()
    cookies = linkcheck.cache.cookie.CookieJar()
    robots_txt = linkcheck.cache.robots_txt.RobotsTxt()
    return aggregator.Aggregate(config, urlqueue, connections,
                                cookies, robots_txt)

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
The WWW Utils Module (:mod:`tendril.utils.www`)
===============================================

This module provides utilities to deal with the internet. All application code
should access the internet through this module, since this where support for
proxies and caching is implemented.

.. rubric:: Main Provided Methods

.. autosummary::

    strencode
    urlopen
    get_soup


This module uses the following configuration values from :mod:`tendril.utils.config`:

.. rubric:: Basic Settings

- :data:`tendril.utils.config.ENABLE_REDIRECT_CACHING` Whether or not redirect caching should be used.
- :data:`tendril.utils.config.TRY_REPLICATOR_CACHE_FIRST` Whether or not a replicator cache should be used.

Redirect caching speeds up network accesses by saving ``301`` and ``302`` redirects,
and not needing to get the correct URL on a second access. This redirect cache is stored
as a pickled object in the ``INSTANCE_CACHE`` folder. The effect of this caching is far
more apparent when a replicator cache is also used.

.. rubric:: Network Proxy Settings

- :data:`tendril.utils.config.NETWORK_PROXY_TYPE`
- :data:`tendril.utils.config.NETWORK_PROXY_IP`
- :data:`tendril.utils.config.NETWORK_PROXY_PORT`
- :data:`tendril.utils.config.NETWORK_PROXY_USER`
- :data:`tendril.utils.config.NETWORK_PROXY_PASS`

.. rubric:: Replicator Cache Settings

The replicator cache is intended to be a ``http-replicator`` instance, to be used to
cache the web pages that are accessed locally. If ``TRY_REPLICATOR_CACHE_FIRST`` is False,
the replicator isn't actually going to be hit.

- :data:`tendril.utils.config.REPLICATOR_PROXY_TYPE`
- :data:`tendril.utils.config.REPLICATOR_PROXY_IP`
- :data:`tendril.utils.config.REPLICATOR_PROXY_PORT`
- :data:`tendril.utils.config.REPLICATOR_PROXY_USER`
- :data:`tendril.utils.config.REPLICATOR_PROXY_PASS`

"""

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

from config import NETWORK_PROXY_TYPE
from config import NETWORK_PROXY_IP
from config import NETWORK_PROXY_PORT
from config import NETWORK_PROXY_USER
from config import NETWORK_PROXY_PASS

from config import ENABLE_REDIRECT_CACHING

from config import TRY_REPLICATOR_CACHE_FIRST
from config import REPLICATOR_PROXY_TYPE
from config import REPLICATOR_PROXY_IP
from config import REPLICATOR_PROXY_PORT
from config import REPLICATOR_PROXY_USER
from config import REPLICATOR_PROXY_PASS

from config import INSTANCE_CACHE

from bs4 import BeautifulSoup
import urllib2

import time
import pickle
import atexit
import os


def strencode(string):
    """
    This function converts unicode strings to ASCII, using python's
    :func:`str.encode`, replacing any unicode characters present in the
    string. Unicode characters which Tendril expects to see in web content
    related to it are specifically replaced first with ASCII characters
    or character sequences which reasonably reproduce the original meanings.

    :param string: unicode string to be encoded.
    :return: ASCII version of the string.

    """
    nstring = ''
    for char in string:
        if char == u'\u00b5':
            char = 'u'
        if char == u'\u00B1':
            char = '+/-'
        nstring += char
    return nstring.encode('ascii', 'replace')


REDIR_CACHE_FILE = os.path.join(INSTANCE_CACHE, 'redirects.p')

try:
    with open(REDIR_CACHE_FILE, "rb") as rdcf:
        redirect_cache = pickle.load(rdcf)
    logger.info('Loaded Redirect Cache from file')
except IOError:
    redirect_cache = {}
    logger.info('Created new Redirect Cache')


def dump_redirect_cache():
    """
    Called during python interpreter shutdown, this function dumps the
    redirect cache to the file system.
    """
    with open(REDIR_CACHE_FILE, 'wb') as f:
        pickle.dump(redirect_cache, f)
    logger.info('Dumping Redirect Cache to file')

if ENABLE_REDIRECT_CACHING is True:
    atexit.register(dump_redirect_cache)


class CachingRedirectHandler(urllib2.HTTPRedirectHandler):
    """
    This handler modifies the behavior of :class:`urllib2.HTTPRedirectHandler`,
    resulting in a HTTP ``301`` or ``302`` status to be included in the ``result``.

    When this handler is attached to a ``urllib2`` opener, if the opening of
    the URL resulted in a redirect via HTTP ``301`` or ``302``, this is reported
    along with the result. This information can be used by the opener to
    maintain a redirect cache.
    """
    def http_error_301(self, req, fp, code, msg, headers):
        """
        Wraps the :func:`urllib2.HTTPRedirectHandler.http_error_301` handler, setting
        the ``result.status`` to ``301`` in case a http ``301`` error is encountered.
        """
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        """
        Wraps the :func:`urllib2.HTTPRedirectHandler.http_error_302` handler, setting
        the ``result.status`` to ``302`` in case a http ``302`` error is encountered.
        """
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result


def _test_opener(openr):
    """
    Tests an opener obtained using :func:`urllib2.build_opener` by attempting to
    open Google's homepage. This is used to test internet connectivity.
    """
    try:
        openr.open('http://www.google.com', timeout=5)
        return True
    except urllib2.URLError:
        return False


def _create_opener():
    """
    Creates an opener for the internet.

    It also attaches the :class:`CachingRedirectHandler` to the opener and sets its
    User-agent to ``Mozilla/5.0``.

    If the Network Proxy settings are set and recognized, it creates the opener and
    attaches the proxy_handler to it. The opener is tested and returned if the test
    passes.

    If the test fails an opener without the proxy settings is created instead and
    is returned instead.
    """
    use_proxy = False
    use_proxy_auth = False
    proxy_handler = None
    proxy_auth_handler = None

    if NETWORK_PROXY_TYPE == 'http':
        use_proxy = True
        proxyurl = 'http://' + NETWORK_PROXY_IP
        if NETWORK_PROXY_PORT:
            proxyurl += ':' + NETWORK_PROXY_PORT
        proxy_handler = urllib2.ProxyHandler({NETWORK_PROXY_TYPE: proxyurl})
        if NETWORK_PROXY_USER is not None:
            use_proxy_auth = True
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, proxyurl, NETWORK_PROXY_USER, NETWORK_PROXY_PASS)
            proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
    if use_proxy:
        if use_proxy_auth:
            openr = urllib2.build_opener(proxy_handler, proxy_auth_handler, CachingRedirectHandler)
        else:
            openr = urllib2.build_opener(proxy_handler, CachingRedirectHandler)
    else:
        openr = urllib2.build_opener(CachingRedirectHandler)
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    if _test_opener(openr) is True:
        return openr
    openr = urllib2.build_opener(CachingRedirectHandler)
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    return openr

opener = _create_opener()


def _create_replicator_opener():
    """
    Creates an opener for the replicator.

    It also attaches the :class:`CachingRedirectHandler` to the opener and sets its
    User-agent to ``Mozilla/5.0``.

    If the Network Proxy settings are set and recognized, it creates the opener and
    attaches the proxy_handler to it, and is returned.
    """

    use_proxy = False
    use_proxy_auth = False
    proxy_handler = None
    proxy_auth_handler = None

    if REPLICATOR_PROXY_TYPE == 'http':
        use_proxy = True
        proxyurl = 'http://' + REPLICATOR_PROXY_IP
        if REPLICATOR_PROXY_PORT:
            proxyurl += ':' + REPLICATOR_PROXY_PORT
        proxy_handler = urllib2.ProxyHandler({REPLICATOR_PROXY_TYPE: proxyurl})
        if REPLICATOR_PROXY_USER is not None:
            use_proxy_auth = True
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, proxyurl, REPLICATOR_PROXY_USER, REPLICATOR_PROXY_PASS)
            proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
    if use_proxy:
        if use_proxy_auth:
            openr = urllib2.build_opener(proxy_handler, proxy_auth_handler, CachingRedirectHandler)
        else:
            openr = urllib2.build_opener(proxy_handler, CachingRedirectHandler)
    else:
        openr = urllib2.build_opener(CachingRedirectHandler)
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    return openr


if TRY_REPLICATOR_CACHE_FIRST is True:
    replicator_opener = _create_replicator_opener()


def urlopen(url):
    """
    Opens a url specified by the ``url`` parameter.

    This function handles :
        - Redirect caching, if enabled.
        - Trying the replicator first, if enabled.
        - Retries upto 5 times if it encounters a http ``500`` error.

    """
    retries = 5
    if ENABLE_REDIRECT_CACHING is True:
        while url in redirect_cache.keys():
            url = redirect_cache[url]
    if TRY_REPLICATOR_CACHE_FIRST is True:
        try:
            page = replicator_opener.open(url)
            try:
                if ENABLE_REDIRECT_CACHING is True and page.status == 301:
                    logger.debug('Detected New Permanent Redirect:\n' +
                                 url + '\n' + page.url)
                    redirect_cache[url] = page.url
            except AttributeError:
                pass
            return page
        except urllib2.HTTPError, e:
            logger.error("HTTP Error : " + str(e.code) + str(url))
            if e.code == 500:
                time.sleep(0.5)
                retries -= 1
            else:
                retries = 0
        except urllib2.URLError, e:
            logger.error("URL Error : " + str(e.errno) + " " + str(e.reason))
            retries = 0

    while retries > 0:
        try:
            page = opener.open(url)
            try:
                if ENABLE_REDIRECT_CACHING is True and page.status == 301:
                    logger.debug('Detected New Permanent Redirect:\n' +
                                 url + '\n' + page.url)
                    redirect_cache[url] = page.url
            except AttributeError:
                pass
            return page
        except urllib2.HTTPError, e:
            logger.error("HTTP Error : " + str(e.code) + str(url))
            if e.code == 500:
                time.sleep(0.5)
                retries -= 1
            else:
                retries = 0
        except urllib2.URLError, e:
            logger.error("URL Error : " + str(e.errno) + " " + str(e.reason))
            retries = 0
    return None


def get_soup(url):
    """
    Gets a :mod:`bs4` parsed soup for the ``url`` specified by the parameter.
    The :mod:`lxml` parser is used.
    """
    page = urlopen(url)
    if page is None:
        return None
    soup = BeautifulSoup(page, 'lxml')
    return soup

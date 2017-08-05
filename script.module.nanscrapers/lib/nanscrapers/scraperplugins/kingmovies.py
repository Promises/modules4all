import re
import requests
import base64
import random
import xbmc
from ..common import random_agent
from ..scraper import Scraper
from ..jsunpack import unpack

class Kingmovies(Scraper):
    domains = ['kingmovies.is']
    name = "kingmovies"
    sources = []

    def __init__(self):
        self.base_link = 'https://kingmovies.is'
        self.api = 'https://api.streamdor.co/sources'

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            heads = {'User-Agent': random_agent()}
            start_url = self.base_link+'/search?q='+title.replace(' ','+')
            html = requests.get(start_url,headers=heads).content
            match = re.compile("<h4 class='item-title'><a href='(.+?)' title='.+?'>(.+?)</a></h4>").findall(html)
            for url2, name in match:
                if title.lower() in name.replace(':','').lower():
                    if (title.lower())[0]==(name.lower())[0]:
                        if 'Season '+season in name:
                            html2 = requests.get(url2,headers=heads).content
                            match2 = re.compile('<li class="ep-item">.+?<a href="(.+?)">(.+?)</a>',re.DOTALL).findall(html2)
                            for url3,name2 in match2:
                                if season in url3:
                                    if len(episode)==1:
                                        episode = '0'+episode
                                    if 'Episode '+episode in name2:
                                        html3 = requests.get(url3,headers=heads).content
                                        match3 = re.compile('<div id="content-embed">.+?src="(.+?)"',re.DOTALL).findall(html3)
                                        for link in match3:
                                            if not link.startswith('http:'):
                                                link = 'http:'+link
                                            self.get_source(link)
            return self.sources
                                        
        except:
            pass
            return []                           

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            heads = {'User-Agent': random_agent()}
            start_url = self.base_link+'/search?q='+title.replace(' ','+')
            html = requests.get(start_url,headers=heads).content
            match = re.compile("<h4 class='item-title'><a href='(.+?)' title='.+?'>(.+?)</a></h4>").findall(html)
            for url2, name in match:
                if title.replace(':','').lower() in name.replace(':','').lower():
                    if year in name:
                        url2 = url2+'/watching.html'
                        html2 = requests.get(url2,headers=heads).text
                        match2 = re.compile('<div id="content-embed">.+?src="(.+?)"',re.DOTALL).findall(html2)                                
                        for link in match2:
                            if not link.startswith('http:'):
                                link = 'http:'+link
                            self.get_source(link)
            return self.sources
        except:
            pass
            return[]

    def get_source(self,link):
        try:
            heads = {'User-Agent': random_agent()}
            List = []
            html3 = requests.get(link,headers=heads).content
            match3 = re.compile('JuicyCodes.Run\((.+?)\);',re.DOTALL).findall(html3)
            for i in match3:
                single = re.compile('"(.+?)"').findall(str(i))
                for s in single:
                    List.append(s)
                html2 = base64.decodestring(str(List).replace('[','').replace(']','').replace('\'','').replace(',','').replace(' ',''))
                try:
                    string= unpack(html2)
                except:
                    pass
                ep_id = re.findall('"episodeID":"(.+?)"',string)[0]
                ep_name = re.findall('"episodeName":"(.+?)"',string)[0]
                ep_backup = re.findall('"episodeBackup":"(.+?)"',string)[0]
                ep_hot = re.findall('"episodeHOT":(.+?),',string)[0]
                File = re.findall('"file":"(.+?)"',string)[0]
                headers = {"origin":"https://embed.streamdor.co",
                           "referer":link,
                           "user-agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36"
                           }
                
                data = {"episodeID":ep_id,
                        "episodeName":ep_name,
                        "episodeBackup":ep_backup,
                        "episodeHOT":ep_hot,
                        "file":File
                        }
                response = requests.post(self.api,headers=headers,data=data).json()
                results = response["sources"]
                try:
                    results.extend(response["sources_backup"])
                except:
                    results = results
                for item in results:
                    playlink = item["file"]
                    quality = item["label"]
                    if '=m' in playlink:
                        source = 'Gvideo'
                    else:
                        source = 'Streamdor'
                    self.sources.append({'source': source, 'quality': quality, 'scraper': self.name, 'url': playlink,'direct': True})
        except:
            pass
Kingmovies()        

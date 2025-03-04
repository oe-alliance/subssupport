# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import html
import requests
import re
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)
import os
from os.path import exists
from urllib.request import Request, urlopen
from urllib.parse import quote_plus, urlencode

from html.parser import HTMLParser
from .IndexsubtitleUtilities import get_language_info
from ..utilities import log

HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
      'Accept': 'application/json, text/javascript, */*; q=0.01',
      'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Origin': 'https://indexsubtitle.cc',
      'Host': 'indexsubtitle.cc',
      'Referer': 'https://indexsubtitle.cc/subtitles/',
      'Upgrade-Insecure-Requests': '1',
      'Connection': 'keep-alive',
      'Accept-Encoding': 'gzip, deflate'}

s = requests.Session()


main_url = "https://indexsubtitle.cc"
url2 = "https://indexsubtitle.cc/subtitlesInfo"
debug_pretext = "indexsubtitle.cc"


indexsubtitle_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi\/Persian': 'Persian'
}


def get_url(url, referer=None):
    if referer is None:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
    else:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0', 'Referer': referer}
    req = Request(url, None, headers)
    response = urlopen(req)
    content = response.read().decode('utf-8')
    response.close()
    content = content.replace('\n', '')
    return content


def find_movie(content, title, year):
    d = content
    print(d)
    url_found = None
    h = HTMLParser()
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        print((tuple(matches.groups())))
        found_title = matches.group('title')
        found_title = html.unescape(found_title)
        print(("found_title", found_title))
        log(__name__, "Found movie on search page: %s (%s)" % (found_title, matches.group('year')))
        if found_title.lower().find(title.lower()) > -1:
            if matches.group('year') == year:
                log(__name__, "Matching movie found on search page: %s (%s)" % (found_title, matches.group('year')))
                url_found = matches.group('link')
                break
    return url_found


def get_rating(downloads):
    rating = int(downloads)
    if (rating < 50):
        rating = 1
    elif (rating >= 50 and rating < 100):
        rating = 2
    elif (rating >= 100 and rating < 150):
        rating = 3
    elif (rating >= 150 and rating < 200):
        rating = 4
    elif (rating >= 200 and rating < 250):
        rating = 5
    elif (rating >= 250 and rating < 300):
        rating = 6
    elif (rating >= 300 and rating < 350):
        rating = 7
    elif (rating >= 350 and rating < 400):
        rating = 8
    elif (rating >= 400 and rating < 450):
        rating = 9
    elif (rating >= 450):
        rating = 10
    return rating


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):  # standard input
    languagefound = lang1
    language_info = get_language_info(languagefound)
    language_info1 = language_info['name']
    language_info2 = language_info['2et']
    language_info3 = language_info['3et']

    subtitles_list = []
    msg = ""

    if len(tvshow) == 0 and year:  # Movie
        searchstring = "%s (%s)" % (title, year)
    elif len(tvshow) > 0 and title == tvshow:  # Movie not in Library
        searchstring = "%s (%#02d%#02d)" % (tvshow, int(season), int(episode))
    elif len(tvshow) > 0:  # TVShow
        searchstring = "%s S%#02dE%#02d" % (tvshow, int(season), int(episode))
    else:
        searchstring = title
    log(__name__, "%s Search string = %s" % (debug_pretext, searchstring))
    get_subtitles_list(searchstring, title, year, language_info2, language_info1, subtitles_list)
    return subtitles_list, "", msg  # standard output


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    language = subtitles_list[pos]["language_name"]
    lang = subtitles_list[pos]["language_flag"]
    name = subtitles_list[pos]["filename"]
    id = subtitles_list[pos]["id"]
    ID = id.split('/')[4]
    ttl = id.split('/')[5]
    id = re.sub("/\\d+$", "", id)
    zp = id.replace('/[^\w ]/', '').replace('/', '_').replace('_subtitles_', '[indexsubtitle.cc]_')
    #print('zp', zp)
    check_data = 'id=' + ID + '&name=' + name + '&lang=' + language + '&url=' + id + ''
    data = s.post(url2, headers=HDR, data=check_data, verify=False, allow_redirects=True).text
    regx = 'download_url":"(.*?)"'
    try:
        download_url = re.findall(regx, data, re.M | re.I)[0]
    except:
        pass
    #print("download_url':",download_url)
    downloadlink = '%s/d/%s/%s/%s/%s.zip' % (main_url, ID, download_url, ttl, zp)
    #print(downloadlink)
    if downloadlink:
        log(__name__, "%s Downloadlink: %s " % (debug_pretext, downloadlink))
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0
        #postparams = { '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid}
        #postparams = urllib3.request.urlencode({ '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        postparams = urlencode({'__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '', '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        #class MyOpener(urllib.FancyURLopener):
            #version = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0'
        #my_urlopener = MyOpener()
        #my_urlopener.addheader('Referer', url)
        log(__name__, "%s Fetching subtitles using url '%s' with referer header and post parameters '%s'" % (debug_pretext, downloadlink, postparams))
        #response = my_urlopener.open(downloadlink, postparams) response.
        response = s.get(downloadlink, headers=HDR, params=postparams, verify=False, allow_redirects=True)
        print(response.content)
        local_tmp_file = zip_subs
        try:
            log(__name__, "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
            if not exists(tmp_sub_dir):
                os.makedirs(tmp_sub_dir)
            local_file_handle = open(local_tmp_file, 'wb')
            local_file_handle.write(response.content)
            local_file_handle.close()
            # Check archive type (rar/zip/else) through the file header (rar=Rar!, zip=PK) urllib3.request.urlencode
            myfile = open(local_tmp_file, "rb")
            myfile.seek(0)
            if (myfile.read(1) == 'R'):
                typeid = "rar"
                packed = True
                log(__name__, "Discovered RAR Archive")
            else:
                myfile.seek(0)
                if (myfile.read(1) == 'P'):
                    typeid = "zip"
                    packed = True
                    log(__name__, "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = True
                    subs_file = local_tmp_file
                    log(__name__, "Discovered a non-archive file")
            myfile.close()
            log(__name__, "%s Saving to %s" % (debug_pretext, local_tmp_file))
        except:
            log(__name__, "%s Failed to save subtitle to %s" % (debug_pretext, local_tmp_file))
        if packed:
            subs_file = typeid
        log(__name__, "%s Subtitles saved to '%s'" % (debug_pretext, local_tmp_file))
        return packed, language, subs_file  # standard output


def prepare_search_string(s):
    s = s.strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title
    s = quote_plus(s)
    return s


def get_subtitles_list(searchstring, title, year, languageshort, languagelong, subtitles_list):
    lang = languagelong
    title = title.strip().lower()
    hrf = quote_plus(title).replace("+", "-").replace(":", "-")
    print('hrf', hrf)
    print('lang', lang)
    url = 'https://indexsubtitle.cc/subtitles/%s' % hrf
    #data = get_url(url,referer=main_url)
    #search_string = prepare_search_string(title)
    #url = getSearchTitle(title, search_string, year)
    try:
        log(__name__, "%s Getting url: %s" % (debug_pretext, url))
        content = get_url(url, referer=main_url)
        print('content', content)
        #content = content.replace('\n','')
    except:
        pass
        log(__name__, "%s Failed to get url:%s" % (debug_pretext, url))
        return
    try:
        log(__name__, "%s Getting '%s' subs ..." % (debug_pretext, languageshort))
        subtitles = re.compile('({"title.+?language":"' + lang + '".+?,{"title)').findall(content)
        #print('subtitles', subtitles)
        ttl = re.compile('ttl = (.+?);').findall(content)[0]
    except:
        log(__name__, "%s Failed to get subtitles" % (debug_pretext))
        return
    for subtitle in subtitles:
        try:
            filename = re.compile('title":"(.+?)"').findall(subtitle)[0]  # .replace("\\/",".")
            filename = filename.strip()
            #print(filename)
            id = re.compile('.*url":"(.+?)"},{"title').findall(subtitle)[0].replace("\/", "/")
            id = id + "/" + ttl
            #print(id)
            try:
                downloads = re.compile('url":"(.+?)"}').findall(subtitle)[0]
                downloads = re.sub("\D", "", downloads)
                #print(downloads)
            except:
                pass
            try:
                rating = get_rating(downloads)
            except:
                rating = 0
                pass

            if not downloads == 0:
                log(__name__, "%s Subtitles found: %s (id = %s)" % (debug_pretext, filename, id))
                subtitles_list.append({'rating': str(rating), 'no_files': 1, 'filename': str(filename), 'id': id, 'sync': False, 'language_flag': languageshort, 'language_name': languagelong})

        except:
            pass
    return

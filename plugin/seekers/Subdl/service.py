# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import print_function


import os
from os.path import exists
import re
import requests
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)
from .SubdlUtilities import get_language_info
from ..utilities import log

HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
      'Content-Type': 'text/html; charset=UTF-8',
      'Host': 'dl.subdl.com',
      'Referer': 'https://www.subdl.com',
      'Upgrade-Insecure-Requests': '1',
      'Connection': 'keep-alive',
      'Accept-Encoding': 'br'}  # , deflate'}


main_url = "https://subdl.com"
debug_pretext = "subdl.com"


subdl_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
}
headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}


def get_url(url, referer=None):
    if referer is None:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
    else:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0', 'Referer': referer}
    content = requests.get(url, None, headers).text
    return content


def get_url2(url, referer=None):
    from urllib.request import urlopen, Request
    req = Request(url)
    response = urlopen(req)
    content = response.read().decode('utf-8')
    #print(content)
    log(__name__, 'Done')
    response.close()
    return content


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
        searchstring = title.replace(' ', '%20').lower()
    log(__name__, "%s Search string = %s" % (debug_pretext, searchstring))
    get_subtitles_list(searchstring, title, language_info2, language_info1, subtitles_list)
    return subtitles_list, "", msg  # standard output


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    language = subtitles_list[pos]["language_name"]
    lang = subtitles_list[pos]["language_flag"]
    id = subtitles_list[pos]["id"]
    url = 'https://dl.subdl.com/subtitle/%s' % (id)
    downloadlink = 'https://dl.subdl.com/subtitle/%s' % (id)
    print(downloadlink)
    if downloadlink:
        log(__name__, "%s Downloadlink: %s " % (debug_pretext, downloadlink))
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0
        postparams = {'__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '', '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid}
        #postparams = urllib3.request.urlencode({ '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        #class MyOpener(urllib.FancyURLopener):
            #version = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0'
        #my_urlopener = MyOpener()
        #my_urlopener.addheader('Referer', url)
        log(__name__, "%s Fetching subtitles using url '%s' with referer header '%s' and post parameters '%s'" % (debug_pretext, downloadlink, url, postparams))
        #response = my_urlopener.open(downloadlink, postparams)
        response = requests.get(downloadlink, data=postparams, headers=HDR, verify=False, allow_redirects=True)
        #print(response.content)
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
            if (myfile.read(1).decode('utf-8') == 'R'):
                typeid = "rar"
                packed = True
                log(__name__, "Discovered RAR Archive")
            else:
                myfile.seek(0)
                if (myfile.read(1).decode('utf-8') == 'P'):
                    typeid = "zip"
                    packed = True
                    log(__name__, "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = False
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


def get_subtitles_list(searchstring, title, languageshort, languagelong, subtitles_list):
    s = languagelong.lower()
    url = '%s/search/%s' % (main_url, searchstring)
    print(("url", url))

    try:
        log(__name__, "%s Getting url: %s" % (debug_pretext, url))
        content = requests.get(url, headers).text
        #print(("content", content))
        subtitles = re.compile('(href="/subtitle/.*?"><div)').findall(content)
        #print(subtitles)
        subtitles = " ".join(subtitles)
        regx = 'href="(.*?)"><div'
        downloadlink = re.findall(regx, subtitles, re.M | re.I)[0]
        #print(downloadlink)
        link = '%s%s/%s' % (main_url, downloadlink, s)
        content = requests.get(link, headers).text
        #print(("content", content))
        subtitles = re.compile('(language":"' + s + '".+?},)').findall(content)
        #print(("subtitles", subtitles))
    except:
        log(__name__, "%s Failed to get subtitles" % (debug_pretext))
        return
    for subtitle in subtitles:
        try:
            filename = re.compile('"title":"(.+?)"').findall(subtitle)[0]
            filename = filename.strip()
            print(filename)

            try:
                id = re.compile('"link":"(.+?)"').findall(subtitle)[0]
                print(id)
            except:
                pass

            if not (filename == 'Εργαστήρι Υποτίτλων' or filename == 'subs4series'):
                log(__name__, "%s Subtitles found: %s (id = %s)" % (debug_pretext, filename, id))
                subtitles_list.append({'filename': filename, 'sync': False, 'id': id, 'language_flag': languageshort, 'language_name': languagelong})

        except:
            pass
    return

# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from urllib.parse import quote_plus, urlencode
import requests
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)
import os
from os.path import exists
from urllib.request import Request, urlopen
from .Moviesubtitles2Utilities import get_language_info
from ..utilities import log

import re


HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
      'Upgrade-Insecure-Requests': '1',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Host': 'www.moviesubtitles.net',
      'Referer': 'https://www.moviesubtitles.net/search.php',
      'Upgrade-Insecure-Requests': '1',
      'Connection': 'keep-alive',
      'Accept-Encoding': 'gzip'}  # , deflate'}

s = requests.Session()


main_url = "https://www.moviesubtitles.net"
main_url2 = "https://www.moviesubtitles.net/subtitles-download"
debug_pretext = "moviesubtitles.net"


moviesubtitles2_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
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
    get_subtitles_list(title, year, language_info2, language_info1, subtitles_list)
    return subtitles_list, "", msg  # standard output


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    language = subtitles_list[pos]["language_name"]
    lang = subtitles_list[pos]["language_flag"]
    id = subtitles_list[pos]["id"]
    url = "%s/%s" % (main_url, id)
    content = s.get(url, headers=HDR, verify=False, allow_redirects=True).text
    #print(content)
    regx = 'name="id" value="(.*?)"'
    try:
        ID = re.findall(regx, content, re.M | re.I)[0]
    except:
        pass
    downloadlink_pattern = 'id=' + ID + '&submit=Download the file'
    post_data = s.post(main_url2, headers=HDR, data=downloadlink_pattern, verify=False, allow_redirects=False).text
    #print("post_data:",post_data)
    regx = 'location.href="(.*?)"'
    try:
        hash = re.findall(regx, post_data, re.M | re.I)[0]
    except:
        pass
    print("hash:", hash)
    downloadlink = 'https://www.moviesubtitles.net/%s' % (hash)
    if downloadlink:
        log(__name__, "%s Downloadlink: %s " % (debug_pretext, downloadlink))
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0
        #postparams = { '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid}
        postparams = urlencode({'__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '', '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        #class MyOpener(urllib.FancyURLopener):
            #version = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0'
        #my_urlopener = MyOpener()
        #my_urlopener.addheader('Referer', url)
        log(__name__, "%s Fetching subtitles using url with referer header '%s' and post parameters '%s'" % (debug_pretext, downloadlink, postparams))
        #response = my_urlopener.open(downloadlink, postparams)
        response = s.get(downloadlink, data=postparams, headers=HDR, verify=False, allow_redirects=True)
        print(response.content)
        local_tmp_file = zip_subs
        try:
            log(__name__, "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
            if not exists(tmp_sub_dir):
                os.makedirs(tmp_sub_dir)
            local_file_handle = open(local_tmp_file, 'wb')
            local_file_handle.write(response.content)
            local_file_handle.close()
            # Check archive type (rar/zip/else) through the file header (rar=Rar!, zip=PK) urllib3.request.urlencode .decode('utf-8')
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


def prepare_search_string(s):
    s = s.strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title
    s = quote_plus(s)
    return s


def get_subtitles_list(title, year, languageshort, languagelong, subtitles_list):
    url = "https://www.moviesubtitles.net/search.php?searchString=%s&start=1" % quote_plus(title)
    dst = languageshort.lower()
    try:
        log(__name__, "%s Getting url: %s" % (debug_pretext, url))
        content = s.get(url, headers=HDR, verify=False, allow_redirects=True).text
        #print(content)
    except:
        log(__name__, "%s Failed to get subtitles" % (debug_pretext))
        return
    try:
        log(__name__, "%s Getting '%s' subs ..." % (debug_pretext, languageshort))
        subtitles = re.compile('(flags/' + dst + '.gif.+?</td></tr><tr)').findall(content)
        #print(("subtitles", subtitles))
    except:
        log(__name__, "%s Failed to get subtitles" % (debug_pretext))
        return
    for subtitle in subtitles:
        try:
            filename = re.compile('<td><a.+?">(.+?)</a>').findall(subtitle)[0]
            filename = filename.strip()
            id = re.compile('href="(.+?)"').findall(subtitle)[0]
            #print(id)
            try:
                downloads = re.compile('.*<td>(.+?) downloads</td></tr><tr').findall(subtitle)[0]
                downloads = re.sub("\D", "", downloads)
            except:
                pass
            try:
                rating = get_rating(downloads)
            except:
                rating = 0
                pass

            if not (downloads == 'Εργαστήρι Υποτίτλων' or downloads == 'subs4series'):
                log(__name__, "%s Subtitles found: %s (id = %s)" % (debug_pretext, filename, id))
                subtitles_list.append({'rating': str(rating), 'no_files': 1, 'filename': filename, 'sync': False, 'id': id, 'language_flag': languageshort, 'language_name': languagelong})

        except:
            pass
    return

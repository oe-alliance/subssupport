# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
import difflib
import os
import re
import string
from bs4 import BeautifulSoup
from .OpensubtitlesmoraUtilities import geturl, get_language_info
from six.moves import html_parser
from six.moves.urllib.request import FancyURLopener
from six.moves.urllib.parse import quote_plus, urlencode
from ..utilities import log
import html
import urllib3
import requests
import re
import requests
import json
import re
import random
import string
import time
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from six.moves import html_parser
warnings.simplefilter('ignore', InsecureRequestWarning)


HDR = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "priority": "u=1, i",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

root_url = 'https://www.opensubtitles.org/en/search/sublanguageid-ara/uploader-morafbi/idmovie-'
main_url = "https://www.opensubtitles.org"
main_download_url = 'https://www.opensubtitles.org/en/subtitleserve/sub/'

s = requests.Session()
debug_pretext = ""
ses = requests.Session()

seasons = ["Specials", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
seasons = seasons + ["Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth", "Sixteenth", "Seventeenth",
                     "Eighteenth", "Nineteenth", "Twentieth"]
seasons = seasons + ["Twenty-first", "Twenty-second", "Twenty-third", "Twenty-fourth", "Twenty-fifth", "Twenty-sixth",
                     "Twenty-seventh", "Twenty-eighth", "Twenty-ninth"]

movie_season_pattern = (r"<a href=\"(?P<link>/subscene/[^\"]*)\">(?P<title>[^<]+)\((?P<year>\d{4})\)</a>\s+"
                        r"<div class=\"subtle count\">\s*(?P<numsubtitles>\d+\s+subtitles)</div>\s+")

# Don't remove it we need it here
opensubtitlesmora_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
}

# def geturl(url):
    # log(__name__, " Getting url: %s" % (url))
    # params = {"query": quote_plus(title) }
    # try:
        # response = requests.get(url, headers=HDR, timeout=10).text
        # content = json.loads(response)
        # print(content)
    # except:
        # log(__name__, " Failed to get url:%s" % (url))
        # content = None
    # return(content)


def getSearchTitle(title, year=None):  # new Add
    title = prepare_search_string(title).replace('%26', '&')
    data_url = 'https://www.opensubtitles.org/libs/suggest.php?format=json3&MovieName=%s' % title
    print(("data_url", data_url))
    content = requests.get(data_url, timeout=10)
    json_response = content.json()
    if len(json_response) == 0:
        print("no data found")
    elif len(json_response) != 0:
        for item in json_response:
            try:
                movie_id = item["id"]
                name = item["name"]
                year = item["year"]
                print(("hrefxxx", movie_id))
                print(("yearxx", year))
                href = root_url + str(movie_id)
                print(("href", href))
                return movie_id

            except:
                break
        return movie_id
    else:
        print("FAILED")


def find_movie(content, title, year):
    url_found = None
    h = html_parser.HTMLParser()
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
                print(url_found)
                break
    return url_found


def find_tv_show_season(content, tvshow, season):
    url_found = None
    possible_matches = []
    all_tvshows = []

    h = html_parser.HTMLParser()
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        found_title = matches.group('title')
        found_title = html.unescape(found_title)
        print(("found_title2", found_title))
        log(__name__, "Found tv show season on search page: %s" % found_title)
        s = difflib.SequenceMatcher(None, string.lower(found_title + ' ' + matches.group('year')), tvshow.lower())
        all_tvshows.append(matches.groups() + (s.ratio() * int(matches.group('numsubtitles')),))
        if found_title.lower().find(tvshow.lower() + " ") > -1:
            if found_title.lower().find(season.lower()) > -1:
                log(__name__, "Matching tv show season found on search page: %s" % found_title)
                possible_matches.append(matches.groups())

    if len(possible_matches) > 0:
        possible_matches = sorted(possible_matches, key=lambda x: -int(x[3]))
        url_found = possible_matches[0][0]
        log(__name__, "Selecting matching tv show with most subtitles: %s (%s)" % (
            possible_matches[0][1], possible_matches[0][3]))
    else:
        if len(all_tvshows) > 0:
            all_tvshows = sorted(all_tvshows, key=lambda x: -int(x[4]))
            url_found = all_tvshows[0][0]
            log(__name__, "Selecting tv show with highest fuzzy string score: %s (score: %s subtitles: %s)" % (
                all_tvshows[0][1], all_tvshows[0][4], all_tvshows[0][3]))

    return url_found


def getallsubs(content, allowed_languages, filename="", search_string=""):
    #content = requests.get(url, timeout=10)
    soup = BeautifulSoup(content.content, "lxml")
    soup1 = soup.find('div', class_="content").h1
    language = soup1.find('span', itemprop="name")
    #more than one sub
    if language is None:
        soup = soup.find('form', method="post").find('table', id="search_results").tbody
        blocks1 = soup.findAll('tr', class_="change even expandable")
        blocks2 = soup.findAll('tr', class_="change odd expandable")
        blocks = blocks1 + blocks2
        i = 0
        subtitles = []
        if len(blocks) == 0:
            print("no data found")
        elif len(blocks) != 0:
            #regex = '''<br/><span title="(?P<releasename>.+?)">.+\s+.+\s.+title="(?P<language>\w+)"><\w+\s.+\s.+<a\shref="(?P<linkid>/\w\w/subtitleserve/sub/\d+)"'''
            for block in blocks:
                language = block.find('td', align="center").a.get("title")
                print(('language', language))
                sub_id = block.find('a', class_="bnone").get('href')
                sub_id = sub_id.split("/")[3]
                print(('sub_id', sub_id))
                sublink = main_download_url + sub_id
                #print(('sublink', sublink))
                releasename = block.find('span').get_text(strip=True)
                print(('releasename', releasename))
                moviename = block.find('a', class_="bnone").get_text(strip=True)
                moviename = re.sub(r'\s+', " ", moviename)
                year = re.search(r'\S+$', moviename)
                year = year.group(0)
                year = re.search(r'\d+', year, re.IGNORECASE | re.DOTALL)
                year = year.group(0)
                print(('moviename', moviename))
                print(('year', year))
                languagefound = language
                language_info = get_language_info(languagefound)
                print(('language_info', language_info))
                if language_info and language_info['name'] in allowed_languages:
                    link = sublink
                    print(('link', link))
                    filename = moviename
                    subtitle_name = str(filename)
                    #print(('subtitle_name', subtitle_name))
                    print(filename)
                    rating = '0'
                    sync = False
                    if filename != "" and filename.lower() == subtitle_name.lower():
                        sync = True
                    if search_string != "":
                        if subtitle_name.lower().find(search_string.lower()) > -1:
                            subtitles.append({'filename': subtitle_name, 'sync': sync, 'link': link,
                                            'language_name': language_info['name'], 'lang': language_info})
                            i = i + 1
                        #elif numfiles > 2:
                            #subtitle_name = subtitle_name + ' ' + ("%d files" % int(matches.group('numfiles')))
                            #subtitles.append({'rating': rating, 'filename': subtitle_name, 'sync': sync, 'link': link, 'language_name': language_info['name'], 'lang': language_info, 'comment': comment})
                        #i = i + 1
                    else:
                        subtitles.append({'filename': subtitle_name, 'sync': sync, 'link': link, 'language_name': language_info['name'], 'year': year, 'lang': language_info})
                        i = i + 1

            subtitles.sort(key=lambda x: [not x['sync']])
            return subtitles
    # one sub only
    elif language is not None:
        soup3 = soup.find('div', class_="content").h3
        i = 0
        subtitles = []
        language = soup1.find('span', itemprop="name").get_text(strip=True)
        language = re.search(r'\S+$', language)
        language = language.group(0)
        print(('language', language))
        sub_id = soup3.find('a', class_="bt-dwl external adds_trigger").get("data-product-id")
        print(('sub_id', sub_id))
        sublink = main_download_url + sub_id
        #print(('sublink', sublink))
        releasename = soup.find('form', method="post").a.get_text(strip=True)
        releasename = re.split('.srt', releasename)[0]
        print(('releasename', releasename))
        moviename = soup.find('a', class_="bt-dwl external adds_trigger").get("data-product-title")
        year = re.search(r'\S+$', moviename)
        year = year.group(0)
        year = re.search(r'\d+', year, re.IGNORECASE | re.DOTALL)
        year = year.group(0)
        print(('moviename', moviename))
        print(('year', year))
        languagefound = language
        language_info = get_language_info(languagefound)
        print(('language_info', language_info))
        if language_info and language_info['name'] in allowed_languages:
            link = sublink
            print(('link', link))
            filename = releasename
            subtitle_name = str(filename)
            #print(('subtitle_name', subtitle_name))
            print(filename)
            rating = '0'
            sync = False
            if filename != "" and filename.lower() == subtitle_name.lower():
                sync = True
            if search_string != "":
                if subtitle_name.lower().find(search_string.lower()) > -1:
                    subtitles.append({'filename': subtitle_name, 'sync': sync, 'link': link,
                                    'language_name': language_info['name'], 'lang': language_info})
                    i = i + 1
                #elif numfiles > 2:
                    #subtitle_name = subtitle_name + ' ' + ("%d files" % int(matches.group('numfiles')))
                    #subtitles.append({'rating': rating, 'filename': subtitle_name, 'sync': sync, 'link': link, 'language_name': language_info['name'], 'lang': language_info, 'comment': comment})
                #i = i + 1
            else:
                subtitles.append({'filename': subtitle_name, 'sync': sync, 'link': link, 'language_name': language_info['name'], 'year': year, 'lang': language_info})
                i = i + 1

        subtitles.sort(key=lambda x: [not x['sync']])
        return subtitles
    else:
        pass


def prepare_search_string(s):
    #s = s.strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title

    s = quote_plus(s)
    return s


def search_movie(title, year, languages, filename):
    root_url = 'https://www.opensubtitles.org/en/search/sublanguageid-ara/uploader-morafbi/idmovie-'
    try:
        title = title.strip()
        print(("title", title))
        title = prepare_search_string(title).replace('%26', '&')
        print(("title", title))
        #url = getSearchTitle(title, year)#.replace("%2B"," ")
        movie_id = getSearchTitle(title, year)
        print(("movie_id", movie_id))
        url = root_url + str(movie_id)
        print(("true url", url))
        #params = {"movieName":linkName}
        content = requests.get(url, timeout=10)
        #print("true url", url)
        #content = geturl(url)
        print(("title", title))
        #print("content", content)
        if content != '':
            _list = getallsubs(content, languages, filename)
            print(("_list", _list))
            return _list
        else:
            return []
    except Exception as error:
        print(("error", error))


def search_tvshow(tvshow, season, episode, languages, filename):
    tvshow = tvshow.strip()
    search_string = prepare_search_string(tvshow)
    search_string += " - " + seasons[int(season)] + " Season"

    log(__name__, "Search tvshow = %s" % search_string)
    url = main_url + "/subtitles/title?q=" + quote_plus(search_string) + '&r=true'
    content, response_url = requests.get(url, headers=HDR, verify=False, allow_redirects=True).text
    if content is not None:
        log(__name__, "Multiple tv show seasons found, searching for the right one ...")
        tv_show_seasonurl = find_tv_show_season(content, tvshow, seasons[int(season)])
        if tv_show_seasonurl is not None:
            log(__name__, "Tv show season found in list, getting subs ...")
            url = main_url + tv_show_seasonurl
            content, response_url = requests.get(url, headers=HDR, verify=False, allow_redirects=True).text
            if content is not None:
                search_string = "s%#02de%#02d" % (int(season), int(episode))
                return getallsubs(content, languages, filename, search_string)


def search_manual(searchstr, languages, filename):
    search_string = prepare_search_string(searchstr)
    url = main_url + "/subtitles/release?q=" + search_string + '&r=true'
    content, response_url = requests.get(url, headers=HDR, verify=False, allow_redirects=True).text

    if content is not None:
        return getallsubs(content, languages, filename)


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):  # standard input
    log(__name__, "%s Search_subtitles = '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" %
         (debug_pretext, file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack))
    if lang1 == 'Farsi':
        lang1 = 'Persian'
    if lang2 == 'Farsi':
        lang2 = 'Persian'
    if lang3 == 'Farsi':
        lang3 = 'Persian'
    if tvshow:
        sublist = search_tvshow(tvshow, season, episode, [lang1, lang2, lang3], file_original_path)
    elif title:
        sublist = search_movie(title, year, [lang1, lang2, lang3], file_original_path)
    else:
        try:
          sublist = search_manual(title, [lang1, lang2, lang3], file_original_path)
        except:
            print("error")
    return sublist, "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    url = subtitles_list[pos]["link"]
    print(("url", url))
    language = subtitles_list[pos]["language_name"]
    filename = subtitles_list[pos]["filename"]
    downloadlink = url
    print(("downloadlink", downloadlink))
    local_tmp_file = filename
    print(("local_tmp_file", local_tmp_file))
    log(__name__, "%s Downloadlink: %s " % (debug_pretext, downloadlink))
    viewstate = 0
    previouspage = 0
    subtitleid = 0
    typeid = "zip"
    filmid = 0
    postparams = {'__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '', '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid}
    log(__name__, "%s Fetching subtitles using url '%s' with referer header '%s' and post parameters '%s'" % (debug_pretext, downloadlink, url, postparams))
    response = requests.get(downloadlink, verify=False, allow_redirects=True)
    local_tmp_file = zip_subs
    try:
        log(__name__, "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
        if not os.path.exists(tmp_sub_dir):
            os.makedirs(tmp_sub_dir)
        local_file_handle = open(local_tmp_file, 'wb')
        local_file_handle.write(response.content)
        local_file_handle.close()
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

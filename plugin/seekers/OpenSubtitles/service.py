# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from urllib.parse import quote_plus
from ..utilities import log
import requests
import difflib
import re
import string
from bs4 import BeautifulSoup
from .OpensubtitlesorgUtilities import get_language_info
from html.parser import HTMLParser
from html import unescape
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore', InsecureRequestWarning)


HDR = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "priority": "u=1, i",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
HDRDL = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "priority": "u=1, i",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

__api = "https://api.subsource.net/api/"

__getMovie = __api + "getMovie"
__getSub = __api + "getSub"
#__search = __api + "searchMovie"
__download = __api + "downloadSub/"
root_url = 'https://www.opensubtitles.org/en/search/sublanguageid-all/idmovie-'
main_url = "https://www.opensubtitles.org"
main_download_url = 'https://www.opensubtitles.org/en/subtitleserve/sub/'

debug_pretext = ""
# Seasons as strings for searching  </div>
# Seasons as strings for searching
seasons = ["Specials", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
seasons = seasons + ["Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth", "Sixteenth", "Seventeenth",
                     "Eighteenth", "Nineteenth", "Twentieth"]
seasons = seasons + ["Twenty-first", "Twenty-second", "Twenty-third", "Twenty-fourth", "Twenty-fifth", "Twenty-sixth",
                     "Twenty-seventh", "Twenty-eighth", "Twenty-ninth"]

movie_season_pattern = ("<a href=\"(?P<link>/subscene/[^\"]*)\">(?P<title>[^<]+)\((?P<year>\d{4})\)</a>\s+"
                        "<div class=\"subtle count\">\s*(?P<numsubtitles>\d+\s+subtitles)</div>\s+")

# Don't remove it we need it here
opensubtitlesorg_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
}


def getSearchTitle(title, year=None):  # new Add
    title = prepare_search_string(title).replace('%26', '&')
    data_url = 'https://www.opensubtitles.org/libs/suggest.php?format=json3&MovieName=%s' % title
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
    h = HTMLParser()
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        print((tuple(matches.groups())))
        found_title = matches.group('title')
        found_title = unescape(found_title)
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

    h = HTMLParser()
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        found_title = matches.group('title')
        found_title = unescape(found_title)
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
    soup = soup.find('form', method="post").find('table', id="search_results").tbody
    blocks1 = soup.findAll('tr', class_="change even expandable")
    blocks2 = soup.findAll('tr', class_="change odd expandable")
    blocks = blocks1 + blocks2
    i = 0
    subtitles = []
    if len(blocks) == 0:
        print("no data found")
    elif len(blocks) != 0:
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
    else:
        print("FAILED")


def prepare_search_string(s):
    #s = s.strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title
    s = quote_plus(s)
    return s


def search_movie(title, year, languages, filename):
    root_url = 'https://www.opensubtitles.org/en/search/sublanguageid-all/idmovie-'
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
    #content = requests.get(url,verify=False,allow_redirects=True).text
    #year = subtitles_list[pos][ "year" ]
    #title = title.strip()
    #search_string = prepare_search_string(title)
    #language = subtitles_list[pos][ "language_name" ]
    #linkName = subtitles_list[pos][ "linkName" ]
    #print(("sub_id", sub_id))
    #print(("language", language))
    #print(("linkName", linkName))
    #params = {"movie":linkName,"lang":language,"id":sub_id}
    #content = requests.post(__getSub, headers=HDR , data=json.dumps(params), timeout=10).text
    #response_json = json.loads(content)
    #content = requests.get(url,headers=HDR,verify=False,allow_redirects=True)
    #downloadlink_pattern = '<!--<span><a class="button"\s+href="(.+)">'
    #match = re.compile(downloadlink_pattern).findall(content)
    #downloadlink = main_url + download_block
    #print(("downloadlink", url))
    #content = geturl(url)
    #downloadlink_pattern = "<a class=\"button\"  href=\"(?P<match>/download/\d+)"
    #match = re.compile(downloadlink_pattern).findall(content)
    #success = response_json['success']
    #if (success == True):
    filename = subtitles_list[pos]["filename"]
    #downloadToken = response_json['sub']['downloadToken']
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
    #postparams = urllib3.request.urlencode({ '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
    #class MyOpener(urllib.FancyURLopener):
        #version = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0'
    #my_urlopener = MyOpener()
    #my_urlopener.addheader('Referer', url)
    log(__name__, "%s Fetching subtitles using url '%s' with referer header '%s' and post parameters '%s'" % (debug_pretext, downloadlink, url, postparams))
    #response = my_urlopener.open(downloadlink, postparams)
    response = requests.get(downloadlink, verify=False, allow_redirects=True)
    local_tmp_file = zip_subs
    try:
        log(__name__, "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
        if not os.path.exists(tmp_sub_dir):
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

# <p align="center">SubsSupport Plugin for Enigma2 (E²)</p>
# <p align="center">![GitHub repo size](https://img.shields.io/github/repo-size/oe-alliance/subssupport.svg) [![Python](https://img.shields.io/badge/Python-3.x-darkviolet.svg?style=flat)](https://python.org) ![Platform](https://img.shields.io/badge/Platform-Enigma2-orange.svg)</p>
Python3 version from the <a href="https://github.com/oe-alliance">OE-Alliance</a> / <a href="https://www.opena.tv">openATV Team</a>, fork of <a href="https://github.com/mx3L/subssupport">mx3L/subssupport</a>.

Subtitles for your movies, series and DVB recordings: search, download, display and sync - all on your Enigma2 receiver.

---

## Github status
[![Build](https://github.com/oe-alliance/subssupport/actions/workflows/oe-alliance-plugins.yml/badge.svg)](https://github.com/oe-alliance/subssupport/actions/workflows/oe-alliance-plugins.yml)
[![Buildbot](https://github.com/oe-alliance/subssupport/actions/workflows/buildbot.yml/badge.svg)](https://github.com/oe-alliance/subssupport/actions/workflows/buildbot.yml)
[![Lint Status](https://github.com/oe-alliance/subssupport/actions/workflows/pylint.yml/badge.svg)](https://github.com/oe-alliance/subssupport/actions/workflows/pylint.yml)
[![Ruff Status](https://github.com/oe-alliance/subssupport/actions/workflows/ruff.yml/badge.svg)](https://github.com/oe-alliance/subssupport/actions/workflows/ruff.yml)
[![AUTOTAG](https://github.com/oe-alliance/subssupport/actions/workflows/tag_release.yml/badge.svg)](https://github.com/oe-alliance/subssupport/actions/workflows/tag_release.yml)

[![Plugin Version](https://img.shields.io/github/v/tag/oe-alliance/subssupport?sort=semver&label=Latest%20Version&color=darkviolet)](https://github.com/oe-alliance/subssupport/tags)
[![Latest Release](https://img.shields.io/github/release-date/oe-alliance/subssupport?label=From&color=darkviolet)](https://github.com/oe-alliance/subssupport/releases/latest)

[![Github last commit](https://img.shields.io/github/last-commit/oe-alliance/subssupport)](https://github.com/oe-alliance/subssupport)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/oe-alliance/subssupport.svg?label=commits)](https://github.com/oe-alliance/subssupport/commits)
[![GitHub stars](https://img.shields.io/github/stars/oe-alliance/subssupport?style=flat)](https://github.com/oe-alliance/subssupport/stargazers)
[![Pull Requests Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat)](https://github.com/oe-alliance/subssupport/pulls)
[![Issues](https://img.shields.io/github/issues/oe-alliance/subssupport?style=flat)](https://github.com/oe-alliance/subssupport/issues)
[![Forks](https://img.shields.io/github/forks/oe-alliance/subssupport?style=flat)](https://github.com/oe-alliance/subssupport/forks)
![Languages](https://img.shields.io/github/languages/top/oe-alliance/subssupport?style=flat)
[![Contributions](https://img.shields.io/github/contributors/oe-alliance/subssupport?style=flat)](https://github.com/oe-alliance/subssupport/graphs/contributors)

## SonarCloud status
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=bugs)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)

[![SonarQube Cloud](https://sonarcloud.io/images/project_badges/sonarcloud-light.svg)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)

---

### 📦 Overview

SubsSupport is an Enigma2 (E²) plugin that brings improved subtitle support to other plugins (e.g. MediaPlayer2 and Kodi) and also works on its own:

- **📥 SubsSupport downloader:** searches about 20 subtitle providers at once, downloads and unpacks the subtitle and loads it into the running video.
- **📺 SubsSupport DVB player:** shows an external subtitle file over a live TV broadcast or a recording, with sync tools.
- **⚙️ SubsSupport settings:** font, colours, background, position, encoding, languages and provider settings.

All three entries are in the plugin menu and in the extensions menu (BLUE). Searches run in a separate process, so the GUI never blocks.

---

### 📜 License Information [![License: GPL v2](https://img.shields.io/badge/License-GPLv2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)

This is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

See [COPYING](COPYING) for full details.

---

### 🚀 Key Features

- 🌐 **Many providers** - free sources without any account plus API providers with free keys, see the table below.
- 🏆 **Best match ranking** - results are ranked by how well the release name fits the playing file (group, resolution, source, codec, edition, year, episode), hash matches first.
- ⚡ **Automatic download** - optionally downloads the best match when playback starts and no subtitle was found (Off / Ask / Automatic, minimum match).
- 🎬 **Title suggestions** via IMDb or OpenSubtitles.com and **TMDB search** with poster and details inside the search screen.
- 🗂️ **Archives** - zip and rar (with unrar), the choice box opens when an archive holds several subtitles.
- 🔤 **Formats** - SubRip (.srt), MicroDVD and SubViewer (.sub), ASS/SSA, WebVTT (.vtt).
- 🔍 **Encoding detection** with charset_normalizer/chardet, limited to the configured encoding group.
- 💾 **Remembered per video** - delay, FPS and a manually chosen encoding.
- 🎨 **Styles** - fonts, many font and background colours, dynamic / static / fixed background, shadow, position.
- 🌍 **Machine translation** of subtitle lines (optional, off by default).
- 📂 **Autoload** - finds `video.srt` and `video.<lang>.srt` next to the video.
- 🖥️ **HD and FHD skins**.

---

### 🌐 Subtitle providers

| **Provider** | **Content** | **Needs** |
| --- | --- | --- |
| OpenSubtitles.com | movies, tv | free API key, username/password optional (more downloads) |
| Subdl | movies, tv | free API key |
| Subsource | movies, tv | free API key (profile page) |
| Wyzie Subs | movies, tv | free API key |
| OpenSubtitles.org | movies, tv | login optional, without VIP downloads come from the website (daily limit) |
| OpenSubtitles (Stremio) | movies, tv | - |
| Gestdown (Addic7ed) | tv | - |
| JustSubtitles | movies (en, ar, de, it, id, ja, ko) | - |
| Titlovi | movies, tv (bs, hr, en, mk, sr, sl) | titlovi.com account |
| Titulky.com | movies, tv (cs, sk) | login optional, a captcha after the daily limit |
| Prijevodi-Online | movies, tv (bs, hr, sr, mk, en) | - |
| Indexsubtitle.cc, Subf2m, Sub_Scene_com, Subtitlecat, Mysubs | movies, tv | - |
| Moviesubtitles.org, Ytssubs | movies | - |
| Subtitlesmora | movies, some episodes (ar) | - |
| LocalDrive | subtitles in the search path and next to the video | - |

API keys and logins are entered in the downloader: BLUE (Settings) > provider settings. YELLOW there tests the login.

---

### 📖 How to Use

**📥 Downloader**

| **Button**    | **Action**        | **Description**                                                      |
|:-------------:| ------------------| ---------------------------------------------------------------------|
| 🔴 **RED**    | Update            | edit title, year, season/episode and languages of the search         |
| 🟢 **GREEN**  | Search            | search all enabled providers                                         |
| 🟡 **YELLOW** | History           | list of the downloaded subtitles                                     |
| 🔵 **BLUE**   | Settings          | search and provider settings (API keys, logins, Test login)          |
| ⚙️ **MENU**   | Context menu      | details of the selected subtitle incl. match score                   |
| ℹ️ **INFO**   | Event info        | TMDB info for the current event (needs the tmdb plugin)              |
| 🆗 **OK**     | Download          | download the selected subtitle and load it                           |
| ❌ **EXIT**   | Back              | cancel the search or close the screen                                |

**📺 DVB player**

| **Button**             | **Action**        | **Description**                                         |
|:----------------------:| ------------------| --------------------------------------------------------|
| 🔴 **RED**             | Subtitle picker   | jump to any line, CH+/CH- first/last line               |
| 🟡 **YELLOW**          | Event sync        | sync the subtitle to the current event                  |
| 🔵 **BLUE**            | FPS               | change the subtitle FPS                                 |
| 🆗 **OK**              | Status            | show/hide the status panel                              |
| ⬅️ ➡️ **LEFT/RIGHT**   | Previous/Next     | previous/next subtitle line                             |
| ⬆️ ⬇️ **UP/DOWN**      | Restart           | restart the current subtitle line                       |
| ⏪ ⏩ **PREV/NEXT**     | -/+ 1 minute      | short press: 1 minute, long press: enter the minutes    |
| ⏯️ **PLAY/PAUSE**      | Pause/Resume      | pause or resume the subtitles                           |
| ⚙️ **MENU**            | Style             | subtitle style settings, applied live                   |
| ℹ️ **INFO**            | Help              | shows all keys                                          |
| ❌ **EXIT**            | Exit              | close the player (with confirmation)                    |

---

### 🛠️ Installation

On openATV and the other OE-Alliance images the plugin is in the feed:

```
opkg update
opkg install enigma2-plugin-extensions-subssupport
```

Runtime packages:

- python3-requests, python3-beautifulsoup4 (providers)
- python3-rarfile and unrar (rar archives)
- python3-twisted-web, python3-pyopenssl, python3-service-identity (HTTPS in the GUI: TMDB, suggestions, translation)
- optional: python3-charset-normalizer (or chardet) for the encoding detection

---

### 🧪 Tests

```
cd test
python3 -m unittest discover -p "test_*.py"
```

Tests against the live provider sites only run with `SUBSSUPPORT_LIVE=1`.

---

### 🌍 Translations

The templates are updated with the **Update translation templates** workflow (Actions tab, run by hand): it regenerates `locale/SubsSupport.pot` and merges it into every `locale/<lang>.po`, then opens a pull request. New texts show up untranslated (English) until someone translates them. Locally the same is done with `cd locale && ./updateallpo.sh`.

---

### 🏷️ Releases

The version is only set in `plugin/__init__.py` (`__version__`, `configure.ac` reads it from there). Raise it - after the push to master the commit is tagged with the version and a GitHub release with the changes is created automatically.

---

### 🙏 Credits

**👨‍💻 Author:**

- original idea and created by <a href="https://github.com/mx3L/subssupport">**mx3L**</a>

**🤝 Contributors:**

- <a href="https://github.com/oe-alliance">**OE-Alliance**</a> / <a href="https://www.opena.tv">**openATV Team**</a> - Python 3 port and maintenance
- <a href="https://github.com/popking159/ssupport">**popking159**</a> - new providers, ASS parser, DVB player features
- and all <a href="https://github.com/oe-alliance/subssupport/graphs/contributors">contributors</a> and translators

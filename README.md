## Subssupport

This is a fork of https://github.com/mx3L/subssupport.

## Build status

[![build](https://github.com/oe-alliance/subssupport/actions/workflows/oe-alliance-plugins.yml/badge.svg)](https://github.com/oe-alliance/subssupport/actions/workflows/oe-alliance-plugins.yml)

## SonarCloud status
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=bugs)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=oe-alliance_subssupport&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=oe-alliance_subssupport)

# Info

subssupport is enigma2 plugin which provides improved subtitles support for several enigma2 plugins. It can also be used as standalone plugin, since it provides subtitles downloader and dvb subtitles player.

## Subtitle providers

| Provider | Content | Needs |
| --- | --- | --- |
| OpenSubtitles.com | movies, tv | free API key, username/password optional (more downloads) |
| Subdl | movies, tv | free API key |
| Subsource | movies, tv | free API key (profile page) |
| Titlovi | movies, tv (bs, hr, en, mk, sr, sl) | titlovi.com account |
| Titulky.com | movies, tv (cs, sk) | login optional, a captcha after the daily limit |
| Prijevodi-Online | movies, tv (bs, hr, sr, mk, en) | - |
| Indexsubtitle.cc, Subf2m, Sub_Scene_com, Subtitlecat, Mysubs | movies, tv | - |
| Moviesubtitles.org, Ytssubs | movies | - |
| Subtitlesmora | movies, some episodes (ar) | - |
| LocalDrive | subtitles in the search path and next to the video | - |

## Requirements

- python3-requests, python3-beautifulsoup4 (seekers)
- python3-rarfile and unrar (rar archives)







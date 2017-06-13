# -*- encoding: utf-8 -*-
import json
import os
import tempfile
import uuid
import urllib
import urllib2
from urllib2 import HTTPError
from xml.etree import ElementTree as ET

from . import NAMESPACE_UUID

APP_ID = uuid.uuid3(NAMESPACE_UUID, 'autovoice')
CLIENT_ID = uuid.uuid4()
M = MALE = 0  # I know, right? So binary normative.
F = FEMALE = 1
_VOICE_PREFIX = 'Microsoft Server Speech Text to Speech Voice '
VOICES = { ('ar-EG', F): _VOICE_PREFIX + '(ar-EG, Hoda)'
         , ('de-DE', F): _VOICE_PREFIX + '(de-DE, Hedda)'
         , ('de-DE', M): _VOICE_PREFIX + '(de-DE, Stefan, Apollo)'
         , ('en-AU', F): _VOICE_PREFIX + '(en-AU, Catherine)'
         , ('en-CA', F): _VOICE_PREFIX + '(en-CA, Linda)'
         , ('en-GB', F): _VOICE_PREFIX + '(en-GB, Susan, Apollo)'
         , ('en-GB', M): _VOICE_PREFIX + '(en-GB, George, Apollo)'
         , ('en-IN', M): _VOICE_PREFIX + '(en-IN, Ravi, Apollo)'
         , ('en-US', F): _VOICE_PREFIX + '(en-US, ZiraRUS)'
         , ('en-US', M): _VOICE_PREFIX + '(en-US, BenjaminRUS)'
         , ('es-ES', F): _VOICE_PREFIX + '(es-ES, Laura, Apollo)'
         , ('es-ES', M): _VOICE_PREFIX + '(es-ES, Pablo, Apollo)'
         , ('es-MX', M): _VOICE_PREFIX + '(es-MX, Raul, Apollo)'
         , ('fr-CA', F): _VOICE_PREFIX + '(fr-CA, Caroline)'
         , ('fr-FR', F): _VOICE_PREFIX + '(fr-FR, Julie, Apollo)'
         , ('fr-FR', M): _VOICE_PREFIX + '(fr-FR, Paul, Apollo)'
         , ('it-IT', M): _VOICE_PREFIX + '(it-IT, Cosimo, Apollo)'
         , ('ja-JP', F): _VOICE_PREFIX + '(ja-JP, Ayumi, Apollo)'
         , ('ja-JP', M): _VOICE_PREFIX + '(ja-JP, Ichiro, Apollo)'
         , ('pt-BR', M): _VOICE_PREFIX + '(pt-BR, Daniel, Apollo)'
         , ('ru-RU', F): _VOICE_PREFIX + '(ru-RU, Irina, Apollo)'
         , ('ru-RU', M): _VOICE_PREFIX + '(ru-RU, Pavel, Apollo)'
         , ('zh-CN', F): _VOICE_PREFIX + '(zh-CN, HuihuiRUS)'
         , ('zh-CN', M): _VOICE_PREFIX + '(zh-CN, Kangkang, Apollo)'
         , ('zh-HK', F): _VOICE_PREFIX + '(zh-HK, Tracy, Apollo)'
         , ('zh-HK', M): _VOICE_PREFIX + '(zh-HK, Danny, Apollo)'
         , ('zh-TW', F): _VOICE_PREFIX + '(zh-TW, Yating, Apollo)'
         , ('zh-TW', M): _VOICE_PREFIX + '(zh-TW, Zhiwei, Apollo)'
         }

_ = urllib2.urlopen('http://api.ipify.org')
X_MSEdge_ClientIP = _.read()
del _


def get(url, params={}, headers={}):
    url += '?' + urllib.urlencode(params)
    request = urllib2.Request(url, headers=headers)
    return urllib2.urlopen(request)

def post(url, data=' ', params={}, headers={}):
    url += urllib.urlencode(params)
    request = urllib2.Request(url, data, headers=headers)
    return urllib2.urlopen(request)

def get_jwt(api_key):
    """Gets a JSON web token for authorization.

    Args:
        api_key (str): The API key for the service to auth with.

    Returns:
        (str) The web token, valid for 15 minutes.

    Raises:
        HTTPError: if the web token could not be fetched.
    
    """
    url = 'https://api.cognitive.microsoft.com/sts/v1.0/issueToken'
    key_header = 'Ocp-Apim-Subscription-Key'
    return post(url, headers={key_header: api_key}).read()

def _save_to_temp_file(response, suffix):
    handle, path = tempfile.mkstemp(suffix, prefix='ankihorse_')
    with os.fdopen(handle, 'wb') as f:
        f.write(response.read())
    #os.close(handle)
    return path

# match japanese punctuation, which bing tts insists on reading out
import re
_punctuation = re.compile(u'[。？.?]')

def bing_tts(jwt, locale, gender, text):
    """TTS from the Microsoft Cognitive Services Bing Speech API.

    Downloads a 16khz 128k bitrate mono mp3 to a temporary file and 
    returns the path to it.


    Args:
        jwt (str): A JSON web token to use for authorization.
        locale (str): The locale of the speaker. A country code of the
            form 'aa-AA', for example 'en-GB', 'ja-JP', ...
        gender (int): The gender of the speaker, either 
            ``ankihorse.cognitive_services.MALE`` or 
            ``ankihorse.cognitive_services.FEMALE``.
        text (str | xml.etree.ElementTree.Element): The text to 
            translate. May contain ``break``, ``emphasis``, and 
            ``prosody`` elements; see the `SSML Specifiation`_.

    Returns:
        (str): The path to the downloaded file.

    _SSML Specification: https://www.w3.org/TR/speech-synthesis/#S3.2.3

    """
    if (locale, gender) not in VOICES:
        raise ValueError('No voice found for locale {} and gender {}'
                         .format(locale, gender))

    # for some reason, bing tts now reads out full stops and question marks
    if locale == 'ja-JP': text = _punctuation.sub('', text)

    url = 'https://speech.platform.bing.com/synthesize'
    headers = { 'Authorization': 'Bearer ' + jwt
              , 'Content-Type': 'application/ssml+xml'
              , 'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
              , 'X-Search-AppID': APP_ID.hex
              , 'X-Search-ClientID': CLIENT_ID.hex
              , 'User-Agent': 'AnkiSRS-AnkiHorse-Plugin'
              }

    speak = ET.Element('speak', version='1.0')
    speak.set('{http://www.w3.org/XML/1998/namespace}lang', locale)
    voice = ET.SubElement(speak, 'voice')
    voice.set('name', VOICES[locale, gender])
    voice.set('{http://www.w3.org/XML/1998/namespace}lang', locale)
    if isinstance(text, ET.Element):
        voice.append(text)
    else:
        voice.text = text

    resp = post(url, headers=headers, data=ET.tostring(speak))
    return _save_to_temp_file(resp, '.mp3')

def bing_image(api_key, locale, query):
    """Images from the Microsoft Cognitive Services Bing Image Search API.

    Downloads the first image result to a temporary file and returns the 
    path to it.

    Args:
        api_key (str): The api key for the Bing Image Search API.
        locale (str): A local string of the form 'aa-AA', for example
            'en-GB', 'ja-JP', ...
        query (str): The query to search for.

    Returns:
        (str): The path to the downloaded file.

    """
    global X_MSEdge_ClientID

    url = 'https://api.cognitive.microsoft.com/bing/v5.0/images/search'
    headers = { 'Ocp-Apim-Subscription-Key': api_key
              , 'User-Agent': 'AnkiSRS-AnkiHorse-Plugin'
              , 'X-MSEdge-Client-IP': X_MSEdge_ClientIP
              }

    params = { 'q': query
             , 'mkt': locale
             }

    resp = get(url, params=params, headers=headers)
    content = json.loads(resp.read())
    image = content['value'][0]
    resp_ = get(image['contentUrl'])
    return _save_to_temp_file(resp_, '.' + image['encodingFormat'])

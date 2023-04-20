'''
lambda_function.py

  Next train for Tokyu Meguro-Line.
  Needs jpholiday package, Time Table of Tokyu Meguro-Line as "mg_timetable.txt"
  2023-03-31
'''
from datetime import datetime, timedelta, timezone
import ast
import jpholiday

TableName = 'mg_timetable.txt'

class BaseSpeech:
    def __init__(self, speech_text, should_end_session, session_attributes=None):
        if session_attributes is None:
            session_attributes = {}
        self._response = {
            'version': '1.0',
            'sessionAttributes': session_attributes,
            'response': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': speech_text
                },
                'shouldEndSession': should_end_session,
            },
        }
        self.speech_text = speech_text
        self.should_end_session = should_end_session
        self.session_attributes = session_attributes
 
    def build(self):
        return self._response

class OneSpeech(BaseSpeech):
    def __init__(self, speech_text, session_attributes=None):
        super().__init__(speech_text, True, session_attributes)
 
 
class QuestionSpeech(BaseSpeech):
    def __init__(self, speech_text, session_attributes=None):
        super().__init__(speech_text, False, session_attributes)
 
    def reprompt(self, text):
        reprompt = {
            'outputSpeech': {
                'type': 'PlainText',
                'text': text
            }
        }
        self._response['response']['reprompt'] = reprompt
        return self

def welcome_response():
    speech_output = "駅はどこですか、上りですか下りですか"
    return QuestionSpeech(speech_output).build()

def doko_dotti_response(s):
    if s == 'doko':
        speech_output = "駅はどこですか"
    if s == 'dotti':
        speech_output = "上りですか下りですか"
    return QuestionSpeech(speech_output).build()

def check_station(st_name):
    st_dic = {
        "不動前": "00007857",
        "西小山": "00004800",
        "洗足"  : "00005276",
        "奥沢"  : "00000803",
        "新丸子": "00004200",
        "元住吉": "00002117"
    }
    for k in st_dic:
        if k == st_name:
            return st_dic[st_name]
    return None

def check_ud(UD):
    if UD not in ("上り", "下り"):
        return None
    r = 0 if UD == "上り" else 1
    return r

def check_slots_value(intent):
    st = intent['slots']['St_Name']['value']
    StCode = check_station(st)
    ud = intent['slots']['UpDown']['value']
    UpDn = check_ud(ud)
    return StCode, UpDn

def train(TBdic, imaHour, imaMinute): # ima is int
    nextTr = []
    nextTr = [ v for v in TBdic[imaHour] if v > imaMinute ]
    l = len(nextTr)
    if imaHour != 0 and l < 3:
        if imaHour == 23:
            imaHour = -1
        nextTr.extend(TBdic[imaHour + 1])
    return nextTr[0:3]

def table(event):
    # set intent & name
    intent = event['request']['intent']
    intent_name = intent['name']
    if intent_name != "SelectTableIntent":
        return
    StCode, UpDn = check_slots_value(intent)
    if StCode is None:
        doko_dotti_response('doko')
        return
    if UpDn is None:
        doko_dotti_response('dotti')
        return

    # タイムゾーンの生成
    JST = timezone(timedelta(hours=+9), 'JST')
    jsttime = datetime.now(JST) + timedelta(minutes=0) # 駅まで0分
    if (jsttime.weekday() >= 5) or jpholiday.is_holiday(jsttime): # yt
        horw = "saturday" # horiday or weekday. Saturday for 東急時刻表ページ
        horw_jp = "休日"
    else:
        horw = "weekday"
        horw_jp = "平日"

    mtt = {}
    with open(TableName, 'r', encoding="utf-8") as f:
        s = f.read()
        mtt = ast.literal_eval(s)

    TBcode = f"{StCode}_{horw}_{UpDn}" # TimeTableCode
    nextTrain = train(mtt[TBcode], jsttime.hour, jsttime.minute)
    if 0 in nextTrain:
        idx = nextTrain.index(0)
        nextTrain[idx] = '0 '

    day = (f'<speak>{horw_jp}の<sub alias="ジコクヒョウデス">時刻表です</sub>。'
           f'次は<say-as interpret-as="time">{nextTrain[0]}分??秒</say-as>,'
           f'<say-as interpret-as="time">{nextTrain[1]}分??秒</say-as>,'
           f'<say-as interpret-as="time">{nextTrain[2]}分??秒</say-as>です。</speak>')

    response = {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': day
            }
        }
    }
    return response

def lambda_handler(event, context):
    request = event['request']
    request_type = request['type']
    
    if request_type == "LaunchRequest":
        return welcome_response()
    if request_type == "IntentRequest":
        return table(event)
    return welcome_response()

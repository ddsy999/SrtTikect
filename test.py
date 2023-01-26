import time
import requests
import datetime as dt
from bs4 import BeautifulSoup


url_dict = {
    'login_page_url': 'https://etk.srail.kr/cmc/01/selectLoginInfo.do?pageId=TK0701000000',
    'home_url': 'https://etk.srail.kr/main.do',
    'schedule_url': 'https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000',
    'checkUserInfoUrl1': 'https://etk.srail.kr/hpg/hra/01/checkUserInfo.do?pageId=TK0101010000',
    'checkUserInfoUrl2': 'https://etk.srail.kr/hpg/hra/02/requestReservationInfo.do?pageId=TK0101030000',
    'checkUserInfoUrl3': 'https://etk.srail.kr/hpg/hra/02/confirmReservationInfo.do?pageId=TK0101030000'
}

request_dict = {
    'header': {
        'Referer': '',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    }
}

login_dict = {
    'data': {
        'srchDvCd': 1,
        'saveCrdNoYn': 'Y'
    }
}

reserve_dict = {
    'rsvTpCd': '01',
    'jobId': '1101',
    'jrnyTpCd': '11',
    'jrnyCnt': '1',
    'totPrnb': '1',
    'stndFlg': 'N',
    'trnOrdrNo1': '',
    'jrnySqno1': '',
    'runDt1': '',
    'trnNo1': '',
    'trnGpCd1': '',
    'stlbTrnClsfCd1': '',
    'dptDt1': '',
    'dptTm1': '',
    'dptRsStnCd1': '',
    'dptStnConsOrdr1': '',
    'dptStnRunOrdr1': '',
    'arvRsStnCd1': '',
    'arvStnConsOrdr1': '',
    'arvStnRunOrdr1': '',
    'scarYn1': 'N',
    'psrmClCd1': '1',
    'smkSeatAttCd1': '000',
    'dirSeatAttCd1': '000',
    'locSeatAttCd1': '000',
    'rqSeatAttCd1': '015',
    'etcSeatAttCd1': '000',
    'psgGridcnt': '1',
    'psgTpCd1': '1',
    'psgInfoPerPrnb1': '1',
    'reqTime': '1670138306170',
    'crossYn': 'N'
}

schedule_data_dict = {
    'stlbTrnClsfCd': '05',
    'trnGpCd': '109',
    'psgNum': '1',
    'seatAttCd': '015',
    'isRequest': 'Y',
    'psgInfoPerPrnb1': '1',
    'psgInfoPerPrnb5': '0'
}

class SRT:

    def __init__(self):
        self.station_list = {}
        
        self.id = '1898954361'
        # ID 입력

        self.pwd = 'wltngozj99!'
        # PWD

        self.departure_time = '05:47'
        self.departures = '수서'
        self.arrivals = '대전'
        self.departure_date = '20230130'
        self.dpt_time_format = self.departure_time[:2] + '0000'

    def crawling(self):
        
        isRunning = True
        while isRunning:
            if not isRunning:
                break

            session = self.login()

            self.set_schedule_data_dict()

            response = session.post(url_dict['schedule_url'], verify=False, headers = request_dict['header'], data = schedule_data_dict)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            data_dict = reserve_dict
            
            for i in soup.find('table').find('tbody').findChildren("tr"):
                isTargetTimeRow = False
                for idx, value in enumerate(i.find_all('td')):
                    if idx == 2:
                        for k in value.find_all('input'):
                            data_dict[k.get('name').split('[')[0]] = k.get('value')
                            data_dict[k.get('name').split('[')[0] + '1'] = k.get('value')

                    deptTime = value.find('em')
                    
                    if deptTime is not None and deptTime.string == self.departure_time:
                        isTargetTimeRow = True

                    if isTargetTimeRow:
                        btn = value.find('a', 'btn_small btn_burgundy_dark val_m wx90')
                        if btn is not None:
                            if btn.find('span').string == '신청하기':
                                data_dict['psrmClCd1'] = '05'
                                data_dict['jobId'] = '1102'

                            data_dict['reqTime'] = int(time.time())
                            data_dict['psrmClCd1'] = '2' if idx == 5 else '1'

                            self.reserve(session, data_dict)

                            isRunning = False
                            return

            print('Refresh')

            time.sleep(3)

    def reserve(self, session, data_dict):
        response = session.post(url_dict['checkUserInfoUrl1'], verify=False, headers = request_dict['header'], data = data_dict)
        response.raise_for_status()

        response = session.get(url_dict['checkUserInfoUrl2'], verify=False, headers = request_dict['header'])
        response.raise_for_status()

        response = session.get(url_dict['checkUserInfoUrl3'], verify=False, headers = request_dict['header'])
        response.raise_for_status()

    def login(self):
        login_dict['data']['srchDvNm'] = self.id
        login_dict['data']['hmpgPwdCphd'] = self.pwd

        request_dict['header']['referer'] = 'https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000'

        session = requests.session()

        response = session.post(url_dict['login_page_url'], verify=False, headers = request_dict['header'], data = login_dict['data'])
        response.raise_for_status()

        response = session.get(url_dict['home_url'], verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        for _, values in enumerate(soup.find('select', id='dptRsStnCd')):
            if values.string.strip() == '' or values.string.strip() == '출발역':
                continue
            self.station_list[values.string] = values.attrs['value']
        
        return session

    def set_schedule_data_dict(self):
        schedule_data_dict['dptRsStnCd'] = self.station_list[self.departures]
        schedule_data_dict['arvRsStnCd'] = self.station_list[self.arrivals]
        schedule_data_dict['dptDt'] = self.departure_date
        schedule_data_dict['dptTm'] = self.dpt_time_format

srt = SRT()
srt.crawling()

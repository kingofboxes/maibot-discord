import requests, re
from pprint import pprint
from bs4 import BeautifulSoup

OPENID_URL = "https://lng-tgk-aime-gw.am-all.net/common_auth/login"
OPENID_POST_URL = "https://lng-tgk-aime-gw.am-all.net/common_auth/login/sid/"

# Exception handler for client
class MaiDXException(Exception):
    pass

# Utility function to get int
def getInt(string):
    _m = re.search("\d+", string)
    if (not _m):
        raise "No int found"
    return int(_m.group(0))

class MaiDXClient:
    def __init__(self):
        self.__session = requests.session()
        self.__loggedin = False

    """ 
    Login with username and password 
    """
    def login(self, user, pwd):
        # Initiate session cookie from am-all.net
        openid_params = {
            "site_id": "maimaidxex",
            "redirect_url": "https://maimaidx-eng.com/maimai-mobile/",
            "back_url": "https://maimai.sega.com/"
        }
        openid_resp = self.__session.get(OPENID_URL, params=openid_params, allow_redirects=False)
        # If we get a redirect, try to login with openid session cookie
        if openid_resp.status_code == 302:
            self.relogin()
            return
        # Do OpenID login
        openid_login_data = {
            "retention": 1,
            "sid": user,
            "password": pwd
        }
        login_resp = self.__session.post(OPENID_POST_URL, data=openid_login_data, allow_redirects=False)
        if login_resp.status_code == 302:
            redir = login_resp.headers['Location']
            if redir.find('maimaidx-eng.com') >= 0:
                # Do maimaidx-eng.com login
                self.__session.get(redir)
                self.__loggedin = True
                return
        raise MaiDXException("Login failed")

    """ 
    Login with am-all.net cookie 
    Requires a prior attempted login
    """
    def relogin(self):
        openid_params = {
            "site_id": "maimaidxex",
            "redirect_url": "https://maimaidx-eng.com/maimai-mobile/",
            "back_url": "https://maimai.sega.com/"
        }
        # OpenID login page GET should redirect to maimaidx-eng
        openid_resp = self.__session.get(OPENID_URL, params=openid_params)
        if openid_resp.status_code == 302:
            redir = openid_resp.headers['Location']
            if redir.find('maimaidx-eng.com') >= 0:
                # Do maimaidx-eng.com login
                self.__session.get(redir)
                self.__loggedin = True
                return

        raise MaiDXException("Login failed")

    """
    player_logo: img.w_112.f_l -> src
    trophy: .trophy_block -> class .trophy_{} = trophy type, text = .trophy_block span
    name: .name_block (get text)
    rating: .rating_block (get text)
    rating_max: div.p_r_5.f_11 (get text)
    star_count: div.p_l_10.f_l.f_14 (get text)
    play_count: div.m_5.m_t_10.t_r.f_12 (get text)
    """
    """
    Get player stats data
    """
    def getPlayerData(self):
        _s = self._validateGet("https://maimaidx-eng.com/maimai-mobile/playerData/")
        return {
            "player_logo": _s.select_one('img.w_112.f_l')['src'],
            "name": _s.select_one('.name_block').get_text(),
            "rating": getInt(_s.select_one('.rating_block').get_text()),
            "rating_max": getInt(_s.select_one('div.p_r_5.f_11').get_text()),
            "star_count": getInt(_s.select_one('div.p_l_10.f_l.f_14').get_text()),
            "play_count": getInt(_s.select_one('div.m_5.m_t_10.t_r.f_12').get_text())
        }

    def _validateGet(self, url):
        # Ensure we're logged in
        if not self.__loggedin:
            raise MaiDXException("Not logged in")

        resp = self.__session.get(url)
        # Test if we get the "error" page, indicates session expiry (login elsewhere)
        _s = BeautifulSoup(resp.text, features='lxml')
        _e = _s.select_one('.main_wrapper > div.container_red.p_10 > div.p_5.f_14')
        if (_e and _e.getText().find('ERROR') >= 0):
            raise MaiDXException("Session has expired")

        return _s
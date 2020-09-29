import requests, re, urllib.parse
from pprint import pprint
from bs4 import BeautifulSoup

OPENID_URL = "https://lng-tgk-aime-gw.am-all.net/common_auth/login"
OPENID_POST_URL = "https://lng-tgk-aime-gw.am-all.net/common_auth/login/sid/"

# Utility function to get int
def getInt(string):
    _m = re.search("\d+", string)
    if (not _m):
        raise "No int found"
    return int(_m.group(0))

class MaiDXException(Exception):
    pass

class MaiDXClient:
    def __init__(self, jar=None):
        self.__session = requests.session()
        self.__loggedin = False
        self.__jar = jar

    def getSessionCookies(self):
        return self.__session.cookies

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
                self.__jar = self.__session.cookies
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
        
        # Update client's jar if session cookies gets updated.
        if len(self.__session.cookies.items()) == 5:
            self.__jar = self.__session.cookies

        # For when a jar is given to the bot upon instantiation.
        self.__session.cookies.update(self.__jar)

        # OpenID login page GET should redirect to maimaidx-eng
        openid_resp = self.__session.get(OPENID_URL, params=openid_params)
        if openid_resp.status_code == 302:
            redir = openid_resp.headers['Location']
            if redir.find('maimaidx-eng.com') >= 0:
                # Do maimaidx-eng.com login
                self.__session.get(redir)
                self.__loggedin = True

    def _validateGet(self, url):

        # Ensure we're logged in
        if not self.__jar and self.__loggedin:
            raise MaiDXException("Not logged in")

        resp = self.__session.get(url, cookies=self.__jar)
        # Test if we get the "error" page, indicates session expiry (login elsewhere)
        _s = BeautifulSoup(resp.text, features='lxml')
        _e = _s.select_one('.main_wrapper > div.container_red.p_10 > div.p_5.f_14')
        
        # Force a relogin if session expired.
        if (_e and _e.getText().find('ERROR') >= 0):
            self.relogin()
            resp = self.__session.get(url)
            _s = BeautifulSoup(resp.text, features='lxml')

        return _s

    """
    player_logo: img.w_112.f_l -> src
    trophy: .trophy_block -> class .trophy_{} = trophy type, text = .trophy_block span
    name: .name_block (get text)
    rating: .rating_block (get text)
    rating_max: div.p_r_5.f_11 (get text)
    star_count: div.p_l_10.f_l.f_14 (get text)
    play_count: div.m_5.m_t_10.t_r.f_12 (get text)
    last_played: span.v_b (second index)
    """
    """
    Get player stats data
    """
    def getPlayerData(self):

        _s = self._validateGet("https://maimaidx-eng.com/maimai-mobile/playerData/")
        _d = self._validateGet("https://maimaidx-eng.com/maimai-mobile/record/")
        _f = self._validateGet("https://maimaidx-eng.com/maimai-mobile/friend/userFriendCode/")
        
        return {
            "_id": _f.select_one('div.m_b_10.p_5.t_c.f_15').get_text(),
            "player_logo": _s.select_one('img.w_112.f_l')['src'],
            "name": _s.select_one('.name_block').get_text(),
            "rating": getInt(_s.select_one('.rating_block').get_text()),
            "rating_max": getInt(_s.select_one('div.p_r_5.f_11').get_text()),
            "star_count": getInt(_s.select_one('div.p_l_10.f_l.f_14').get_text()),
            "play_count": getInt(_s.select_one('div.m_5.m_t_10.t_r.f_12').get_text()),
            "last_played": _d.select('span.v_b')[1].get_text()
        }

    """
    Each song is contained in: 'div.w_450.m_15.p_r.f_0':
    Genre/categories -> 'screw_block.m_15.f_15'
    Diffculty is obtained via: img.h_20.f_l -> src (regex search to obtain diff).
    song: div.t_l.f_13.break (get text)
    diff: see above
    map: img.music_kind_icon -> src (in the case that a deluxe and standard map exists, use backup search of '_btn_on') 
    level: div.f_r.t_c.f_14 (get text)
    score: div.w_120.t_r.f_l.f_12 (get text)
    rank: img.h_30.f_r (also comes with FC/FC+ and AP/AP+, always the 2nd index) -> src (regex search to obtain rank)
    """
    """
    Get entire play record (with scores) and song list from maimai DX NET
    """
    def getPlayerRecord(self):
        
        # First pass variable to remove redundancy.
        # List holds dictionaries corresponding to tracks.
        firstPass = True
        _id = 0
        _db = []
        _diff = {
            0 : "BASIC",
            1 : "ADVANCED",
            2 : "EXPERT",
            3 : "MASTER",
            4 : "REMASTER"
        }
        
        # Loop through the URL ending in a defined range for scores based on difficulty.
        for i in range(2, 5):

            # Obtain relevant div blocks.
            _s = self._validateGet(f'https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff={i}')
            _r = _s.select('div.w_450.m_15.p_r.f_0')
            _t = _s.select('div:is(.screw_block.m_15.f_15, .w_450.m_15.p_r.f_0)')

            # Obtain difficulty from i.
            diff = _diff[i]
            
            # _t contains every tag corresponding to song or genre, so loop through it.
            for tag in _t:

                # Assume tag is song, and obtain the div.
                record = None
                song = tag.select_one('div.music_name_block.t_l.f_13.break')

                # If no valid object is returned, it is a genre.
                if not song:
                    genre = tag.get_text()
                else:
                    song = tag.select_one('div.t_l.f_13.break').get_text()
                    
                    # Get map version.
                    version = tag.select_one('img.music_kind_icon')
                    if not version:
                        version = tag.find(class_=re.compile('_btn_on'))
                    version = re.search('music_(.*)\.png', version['src']).group(1).upper()
                    version = "DELUXE" if version == "DX" else "STANDARD"

                    # Check if a score exist, if so, extract score and rank.
                    score = tag.select_one('div.w_120.t_r.f_l.f_12')
                    if score:
                        rank_div = tag.select('img.h_30.f_r')
                        rank = re.search('icon_(.*)\.png', rank_div[2]['src']).group(1)
                        rank = rank[:-1].upper() + '+' if rank[-1] == 'p' else rank[:].upper()
                        score = score.get_text()
                        value = float(score[:-1])
                    else:
                        score = None
                        rank = None
                        value = None
                    
                    # Create dictionary on first pass or append the new difficulty information on subsequent passes.
                    if firstPass:
                        record = {
                            "_id" : _id,
                            "song": song,
                            "genre": genre,
                            "version": version,
                            "records": {
                                diff : {
                                    "level": tag.select_one('div.f_r.t_c.f_14').get_text(),
                                    "rank" : rank,
                                    "score": score,
                                    "value" : value
                                }
                            }
                        }
                        _id += 1
                    else:
                        for d in _db:
                            if d['song'] == song and d['genre'] == genre and d['version'] == version:
                                record = d
                                break
                        
                        record['records'][diff] = {
                            "level": tag.select_one('div.f_r.t_c.f_14').get_text(),
                            "rank" : rank,
                            "score": score,
                            "value" : value
                        }
                
                if record and firstPass:
                    _db.append(record)
            
            firstPass = False

        return _db

    # Get a list of the 50 most recent songs that the user has played.
    def getPlayerHistory(self):
        _db = []
        for i in range(0, 50):
            _s = self._validateGet(f'https://maimaidx-eng.com/maimai-mobile/record/playlogDetail/?idx={i}')

            # Get difficulty via icon url:
            diff_div = _s.select_one('img.playlog_diff.v_b')
            diff = re.search('.*/diff_(.*)\.png', diff_div['src']).group(1).upper()

            # Get rank via icon url:
            rank_div = _s.select_one('img.playlog_scorerank')
            rank = re.search('.*/(.*)\.png', rank_div['src']).group(1)
            rank = rank[:-4].upper() + '+' if 'plus' in rank else rank[:].upper()

            # Get map via icon url:
            version_div = _s.select_one('img.playlog_music_kind_icon')
            version = re.search('.*/(.*)\.png', version_div['src']).group(1)
            version = "Deluxe" if 'dx' in version else "Standard"

            # Return a record as a dictionary.
            record = {
                'song': _s.select_one('div.m_5.p_5.p_l_10.f_13').get_text(),
                'score': _s.select_one('div.playlog_achievement_txt.t_r').get_text(),
                'version' : version.upper(),
                'diff' : diff,
                'rank' : rank,
                'fast' : int(_s.select('div.p_t_5')[0].get_text()),
                'late' : int(_s.select('div.p_t_5')[1].get_text()),
                'time_played': _s.select('span.v_b')[1].get_text(),
                'song_icon' : _s.select_one('img.music_img.m_5.m_r_0.f_l')['src']
            }
            _db.append(record)
        
        # Return a db sorted by time played (latest to earliest).
        _db = sorted(_db, key = lambda x : x['time_played'], reverse = True)
        for i, _r in enumerate(_db):
            _r['_id'] = i
        return _db

    def getImageURLs(self):
        
        # Obtain relevant div blocks.
        _id = 0
        _db = []
        _s = self._validateGet(f'https://maimaidx-eng.com/maimai-mobile/record/musicGenre/search/?genre=99&diff=0')
        _r = _s.select('div.w_450.m_15.p_r.f_0')
        
        # _t contains every tag corresponding to song or genre, so loop through it.
        for r in _r:

            idx = r.select_one('input')
            suffix = urllib.parse.quote(f"{idx['value']}", safe='')
            _s = self._validateGet(f"https://maimaidx-eng.com/maimai-mobile/record/musicDetail/?idx={suffix}")

            print(_id)
            
            record = {  '_id': _id,
                        'song' : _s.select_one('div.m_5.f_15.break').get_text(),
                        'genre' : _s.select_one('div.m_10.m_t_5.t_r.f_12.blue').get_text(),
                        'url' : _s.select_one('img.w_180.m_5.f_l')['src'] }
            
            _id += 1
            _db.append(record)

        return _db
                
                
                
            
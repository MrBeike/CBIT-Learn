import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
from datetime import datetime
import ddddocr
from urllib.parse import urlencode


class CBIT:
    def __init__(self) -> None:
        self.s = requests.session()
        self.s.headers = {
            "Host": "learning.cbit.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "isapp": "0",
            "apikey": "2456269a445b4a18afad29fd12714da2",
        }

    @staticmethod
    def aes(text: str) -> str:
        """
        登录过程中需要使用到的AES加密算法

        Args:
            text (str): 待加密的文本

        Returns:
            str: aes加密后的结果
        """
        datekey = b"dacf107e4bdbbef0"
        dateiv = b"bcancid682e09aec"
        text_bytes = text.encode("utf-8")
        text_bytes_padded = pad(text_bytes, AES.block_size, "pkcs7")
        aes = AES.new(datekey, AES.MODE_CBC, dateiv)
        en_bytes = aes.encrypt(text_bytes_padded)
        en_bytes_base64 = base64.b64encode(en_bytes)
        en_text = en_bytes_base64.decode("utf-8")
        return en_text

    def initialPage(self) -> bytes:
        """
        首次访问获取必要信息

        Returns:
            bytes: 验证码内容字节
        """
        # 访问主页获取cookie等初始状态
        home_url = "https://learning.cbit.com.cn/www/views/index/index.html"
        self.s.get(home_url).content.decode("utf-8")

        # 初始验证码页面
        get_sessionId_cookie_url = "https://learning.cbit.com.cn/www/views/checking.jsp"
        code = self.s.get(get_sessionId_cookie_url).content
        self.sessionId = self.s.cookies.get("sessionIdCookie", default="None")
        with open("code.png", "wb") as f:
            f.write(code)
        return code

    def codeChange(self) -> bytes:
        """
        验证码刷新

        Returns:
            bytes: 验证码内容字节
        """

        # 构建GMT格式时间 用于后续POST请求
        gmt_format = "%a %b %d %Y %H:%M:%S GMT 0800 (中国标准时间)"
        gmt_time = datetime.now().strftime(gmt_format)

        # 刷新验证码
        new_code_url = "https://learning.cbit.com.cn/www/views/checking.jsp"
        params = {"dt": gmt_time}
        code = self.s.get(new_code_url, params=params).content
        self.sessionId = self.s.cookies.get("sessionIdCookie", default="None")
        with open("code.png", "wb") as f:
            f.write(code)
        return code

    @staticmethod
    def codeRecognize(code: bytes | str) -> str:
        """
        验证码识别

        Args:
            code (bytes | str): 待识别的验证码，图片字节码|图片文件名

        Returns:
            str: 验证码识别结果
        """
        # 验证码识别（ddddocr)
        ocr = ddddocr.DdddOcr()
        if isinstance(code, str):
            with open(code, "rb") as f:
                code = f.read()
        code_text = ocr.classification(code)
        return code_text

    # 登录函数
    def login(self, username: str, password: str, code: str) -> dict:
        """
        登录函数

        Args:
            username (str): 用户名
            password (str): 密码
            code (str): 验证码

        Returns:
            dict: 登录后获取的用户信息
        """
        # 添加headers
        self.s.headers["X-Requested-With"] = "XMLHttpRequest"
        self.s.headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
        login_url = "https://learning.cbit.com.cn/www//login/userlogin.do"
        data = {
            "username": self.aes(username),
            "password": self.aes(password),
            "yzm": code,
            "convHtmlField": "username,password",
            "loginType": "pcLogin",
            "sessionID": self.sessionId,
        }
        login_data = self.s.post(login_url, data=data).json()
        return login_data

    def getMyCenter(self, loginData: dict) -> dict:
        """
        获取个人中心中的线上培训班课程信息

        Args:
            loginData (dict): 登录成功后返回的用户信息

        Returns:
            dict: 线上培训详细信息
        """
        # 更新headers
        self.s.headers["token"] = loginData["token"]
        # 登录验证成功后，带token访问网址，获取新JSESSIONID
        get_cookie_url = "https://learning.cbit.com.cn/www/login/selectUserGroup.do"
        self.s.post(get_cookie_url)
        # 更新headers
        param = {"name": loginData["name"], "groupName": loginData["groupName"]}
        my_center_training_url = (
            "https://learning.cbit.com.cn/www/views/myCenter/training.html"
        )

        referer = f"{my_center_training_url}?{urlencode(param)}"
        self.s.headers["Referer"] = referer
        # 个人中心 class1
        # tc_mode 724：默认线上培训班  725：面授培训班[https://learning.cbit.com.cn/www/views/js/myCenter/mytraining.js]
        self.s.headers["Content-Type"] = (
            "application/x-www-form-urlencoded; charset=UTF-8"
        )
        get_training_url = (
            "https://learning.cbit.com.cn/www/myTrainingClass/getMyTrainingClass.do"
        )

        data = {
            "tc_mode": "724",
            "pageIndex": "1",
            "pageSize": "4",
            "trainingtime": "0",
        }
        training_info = self.s.post(get_training_url, data=data).json()
        return training_info

    def getTraining(self, trainingInfo: dict, index: int = 0) -> dict:
        """
        获取指定培训课程详细信息

        Args:
            trainingInfo (dict): 获取到的线上培训详细信息
            index (int, optional):指定培训班序号. Defaults to 0.

        Returns:
            dict: 特定培训课程详细信息
        """
        # 获取tc_id training class?
        tc_id = trainingInfo["mytrainingclass"][index]["tc_id"]
        # 获取培训班详情 class2
        training_detail_url = (
            "https://learning.cbit.com.cn/www/onlineTraining/trainingdetails.do"
        )

        params = {"id": tc_id}
        training_detail = self.s.get(training_detail_url, params=params).json()
        return training_detail

    def getLesson(self, trainingDetail: dict, index: int = 0) -> dict:
        """
        获取指定课程的详细信息

        Args:
            trainingDetail (dict): 获取到的指定培训信息
            index (int, optional): 培训中的课程序号. Defaults to 0.

        Returns:
            dict: 指定课程详细信息
        """
        tc_id = trainingDetail["trainingdetails"]["id"]
        # 培训课程列表
        training_lesson = trainingDetail["traininglesson"]
        # 选取特定子课程 class3
        select_training_lession = training_lesson[index]
        lessonId = select_training_lession["id"]
        le_name = select_training_lession["le_name"]
        print(lessonId, le_name)
        self.s.headers["Referer"] = (
            f"https://learning.cbit.com.cn/www/views/lesson/lessonDetailsStudeyed.html?tcid={tc_id}&lessonId={lessonId}"
        )
        # 课程详情
        lession_detail_url = (
            "https://learning.cbit.com.cn/www//lessonDetails/details.do"
        )
        data = {
            "tcid": tc_id,
            "lessonId": lessonId,
        }
        lesson_detail = self.s.post(lession_detail_url, data=data).json()
        # 存储tc_id
        lesson_detail["tc_id"] = tc_id
        return lesson_detail

    def getVideo(self, lessonDetail: dict, index: int) -> dict:
        """
        获取指定课程内的视频信息

        Args:
            lessonDetail (dict): 获取到的课程信息
            index (int): 课程内视频序号.Defaults to 0.

        Returns:
            dict: 指定视频信息
        """
        # 子课程里的所有视频 class4
        tc_id = lessonDetail["tc_id"]
        le_id = lessonDetail["lessonitem"][index]["le_id"]
        itemId = lessonDetail["lessonitem"][index]["id"]
        # 视频详细信息
        video_page_url = "https://learning.cbit.com.cn/www/pc/index.do"
        data = {
            "le_id": le_id,
            "itemid": itemId,
            "current": "0",
            "tcid": tc_id,
        }
        video_detail = self.s.post(video_page_url, data=data).json()
        # 存储tc_id
        video_detail["tc_id"] = tc_id
        return video_detail

    def learn(self, videoDetail: dict) -> dict:
        """
        视频学习

        Args:
            videoDetail (dict): 获取到的视频信息

        Returns:
            dict: 视频学习结果
        """
        totalTime = videoDetail["ALL_TIMES"]
        suspendTime = videoDetail["studyplan"]
        studyTime = totalTime
        tc_id = videoDetail["tc_id"]
        for item in videoDetail["items"]:
            lessonId = item["leid"]
            itemId = item["id"]
        # 学习视频
        video_url_url = f"https://learning.cbit.com.cn/www/lessonDetails/updateLessonProcessPC.do?lessonId={lessonId}&lessonItemId={itemId}&process=-2&tcid={tc_id}&totalTime={totalTime}&suspendTime={totalTime}&studytime={totalTime}"
        learn_result = self.s.post(video_url_url).json()
        return learn_result

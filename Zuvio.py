import datetime
import random
import time
import winsound
import json
import os, sys

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

chrome_options = webdriver.ChromeOptions()

prefs = {"profile.managed_default_content_settings.images": 2,
         "profile.default_content_setting_values.notifications": 2,
         "profile.managed_default_content_settings.stylesheets": 2,
         "profile.managed_default_content_settings.cookies": 2,
         "profile.managed_default_content_settings.javascript": 1,
         "profile.managed_default_content_settings.plugins": 1,
         "profile.managed_default_content_settings.popups": 2,
         "profile.managed_default_content_settings.geolocation": 2,
         "profile.managed_default_content_settings.media_stream": 2,
         }
chrome_options.add_experimental_option("prefs", prefs)

chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
chrome_options.add_argument('log-level=3')
# LOGGER.setLevel(logging.WARNING)

l = "=" * 35
BANNER = f"{l}\nZuvio自動點名小幫手\nhttps://github.com/opabravo/zuvio\n\n歡迎來git pull & create issues~\n{l}\n"

try:
    DRIVER = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=chrome_options)
except Exception:
    input("error loading driver!!!\n\n" + sys.exc_info()[0])
    exit(1)

URI = "https://irs.zuvio.com.tw/student5/irs/rollcall/{}"
CALL_COUNT = 0


class Courses:
    def __init__(self):
        pass

    def get_courses(self):
        DRIVER.get("https://irs.zuvio.com.tw/student5/irs/index")
        courses = DRIVER.find_elements(By.CLASS_NAME, 'i-m-p-c-a-c-l-c-b-t-course-name')

        # Remove trash courses
        for x in courses:
            if "大學生" in x.text:
                courses.remove(x)
                break

        course_ids = [x.get_attribute("data-course-id") for x in courses]
        course_names = [x.text for x in courses]
        data = dict(zip(course_ids, course_names))
        return data

    def select_course(self, courses: dict):
        for id, name in courses.items():
            print(f"{courses.index(id) + 1} - {name}")

        i = int(input(f"\n{'-' * 20}\n\nSelect ~> ")) - 1
        courses.get()
        selected_course = courses.keys()[i]
        return selected_course

    def print_courses(self, courses):
        for k, v in courses.items():
            print(f"[{k}] {v}")
        print(f"\n{'-' * 20}\n")


class Login:

    def start_login(self, user, passwd):
        DRIVER.find_element(By.ID, "email").send_keys(user)
        DRIVER.find_element(By.ID, "password").send_keys(passwd)
        DRIVER.find_element(By.ID, "login-btn").submit()
        return str(DRIVER.page_source)

    def login_by_request(self):
        email = input("帳號 : ")
        if "@gcloud" in email: # redirect to google login method
            return self.google_login()

        password = input("密碼 : ")

        WebDriverWait(DRIVER, 10).until(EC.presence_of_element_located((By.ID, 'login-btn')))
        page = self.start_login(email, password)

        if "全部課程" not in page:
            print("帳號或密碼錯誤!\n")
            self.login_by_request()
        else:
            print("登入成功!!\n")
            save_login(email, password)

    def get_cookies(self, driver):
        driver.get("https://irs.zuvio.com.tw/")
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'i-m-p-c-a-title-box')))
        cookies = driver.get_cookies()
        return cookies

    def google_login(self):
        input("\n由於使用Google自動登入將面臨 不明裝置驗證、人機驗證 等不穩定之因素\n請手動登入!!\n> 按[ENTER]跳轉")
        driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
        cookies = self.get_cookies(driver)
        driver.quit()
        #if ".irs.zuvio.com.tw" not in cookies[0]["domain"]:
        #    input("\n未成功登入!請重新嘗試\n[ENTER]..")
        #    return self.google_login()

        DRIVER.delete_all_cookies()
        for cookie in cookies:
            DRIVER.add_cookie(cookie)
        DRIVER.refresh()

    def login_by_saved(self):
        cfg = load_login()
        page = self.start_login(cfg['user'], cfg['pass'])

        if "全部課程" not in page:
            os.remove("settings.json")
            print("已移儲存的無效帳密，請重新輸入帳密\n")
            return self.login_by_request()

        print("登入成功!!\n")

    def login(self):
        DRIVER.get("https://irs.zuvio.com.tw/")
        if os.path.exists("settings.json"):
            self.login_by_saved()
        else:
            self.login_by_request()


class Zuvio(Courses, Login):

    def call_result(self, course_id):
        DRIVER.get(URI.format(course_id))  # Fill the course ID
        page_source = DRIVER.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        result = soup.find("div", class_="irs-rollcall")
        # print(result)
        return result

    def submit_call(self, course_name):
        winsound.Beep(1500, 500)
        winsound.Beep(1500, 1000)

        try:
            DRIVER.find_element(By.ID, "submit-make-rollcall").click()
            print(f'[{datetime.datetime.now().time()}] ~> {course_name} | 已成功點名!!!\n')
        except Exception as e:
            print(str(e))
            pass

    def monitor_rollcall(self, courses, course_id):
        during_call = False

        print(f"已選擇 - {courses[course_id]}({course_id})")
        print("正在等待點名開始...")

        while True:
            result = self.call_result(course_id)

            if during_call:  # Override the role call
                if "目前未開放簽到" not in str(result): continue
                during_call = False
                print(f"[{datetime.datetime.now().time()}] 點名結束\n")

            if "簽到開放中" in str(result):
                during_call = True
                self.submit_call(courses[course_id])

            DRIVER.refresh()
            time.sleep(random.randint(7, 16))

    def monitorCalls(self, courses):
        for id, name in courses.items():
            result = self.call_result(id)
            if "簽到開放中" in str(result):
                self.submit_call(name)

            time.sleep(random.randint(1, 3))


def save_login(user, passwd):
    d = {'user': user, 'pass': passwd}
    with open('settings.json', 'w') as fp:
        json.dump(d, fp)


def load_login():
    with open('settings.json', 'r') as fp:
        data = json.load(fp)
    return data


os.system('cls')
print(BANNER)

try:
    zuvio = Zuvio()
    zuvio.login()
    courses = zuvio.get_courses()

    if len(sys.argv) == 2:
        course_id = zuvio.select_course(courses)
        zuvio.monitor_rollcall(courses, course_id)
    else:
        zuvio.print_courses(courses)
        print(f"最大誤差值 : {3 * (len(courses) - 1)}秒\n")  # Max : 3*(len(courses)-1)
        print(f"正在 {len(courses)} 門課程中等待點名...")

        while 1:
            zuvio.monitorCalls(courses)

except KeyboardInterrupt:
    input("\nExited...")

except TimeoutException:
    print("連線逾時")
    pass

except Exception as e:
    raise

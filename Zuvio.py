import datetime
import random
import time
import winsound
import json
import os, sys

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

chrome_options = webdriver.ChromeOptions()

prefs = {"profile.managed_default_content_settings.images":2,
         "profile.default_content_setting_values.notifications":2,
         "profile.managed_default_content_settings.stylesheets":2,
         "profile.managed_default_content_settings.cookies":2,
         "profile.managed_default_content_settings.javascript":1,
         "profile.managed_default_content_settings.plugins":1,
         "profile.managed_default_content_settings.popups":2,
         "profile.managed_default_content_settings.geolocation":2,
         "profile.managed_default_content_settings.media_stream":2,
}
chrome_options.add_experimental_option("prefs",prefs)

chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--headless')
chrome_options.add_argument('log-level=3')
#LOGGER.setLevel(logging.WARNING)

l = "="*35
BANNER = f"{l}\nZuvio自動點名小幫手\nhttps://github.com/opabravo/zuvio\n\n還迎來git pull & create issues~\n{l}\n"

try:
    DRIVER = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=chrome_options)
except Exception:
    print("error loading driver!!!\n\n" + sys.exc_info()[0])
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

    def select_course(self, courses:dict):
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

def login():
    #print("進入登入頁")
    DRIVER.get("https://irs.zuvio.com.tw/")

    def start_login(user, passwd):
        DRIVER.find_element(By.ID, "email").send_keys(user)
        DRIVER.find_element(By.ID, "password").send_keys(passwd)
        DRIVER.find_element(By.ID, "login_btn").submit()
        return str(DRIVER.page_source)

    def request_login():
        email = input("帳號 : ")
        passwd = input("密碼 : ")
        page = start_login(email, passwd)

        if "全部課程" not in page:
            print("帳號或密碼錯誤!\n")
            request_login()
        else:
            print("登入成功!!\n")
            save_login(email, passwd)

    def saved_login():
        cfg = load_login()
        page = start_login(cfg['user'], cfg['pass'])

        if "全部課程" not in page:
            os.remove("settings.json")
            print("已移儲存的無效帳密，請重新輸入帳密\n")
            return request_login()

        print("登入成功!!\n")
    
    if os.path.exists("settings.json"):
        saved_login()
    else:
        request_login()

def save_login(user, passwd):
    d = {'user':user, 'pass':passwd}
    with open('settings.json', 'w') as fp:
        json.dump(d, fp)

def load_login():
    with open('settings.json', 'r') as fp:
        data = json.load(fp)
    return data

def call_result(course_id):
    DRIVER.get(URI.format(course_id))  # Fill the course ID
    page_source = DRIVER.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    result = soup.find("div", class_="irs-rollcall")
    # print(result)
    return result

def submit_call(course_name):
    winsound.Beep(1500, 500)
    winsound.Beep(1500, 1000)

    try:
        DRIVER.find_element(By.ID, "submit-make-rollcall").click()
        print(f'[{datetime.datetime.now().time()}] ~> {course_name} | 已成功點名!!!\n')
    except Exception as e:
        print(repr(e))
        pass

def monitor_rollcall(courses, course_id):
    during_call = False

    print(f"已選擇 - {courses[course_id]}({course_id})")
    print("正在等待點名開始...")

    while True:

        result = call_result(course_id)

        if(during_call==True):  # Override the role call
            if ("目前未開放簽到" not in str(result)): continue      
            during_call = False
            print(f"[{datetime.datetime.now().time()}] 點名結束\n")
        
        if ("簽到開放中" in str(result)):
            during_call = True
            submit_call(courses[course_id])
                
        DRIVER.refresh()
        time.sleep(random.randint(7, 16))

def monitorCalls(courses):

    for id, name in courses.items():
            result = call_result(id)
            
            if ("簽到開放中" in str(result)):
                submit_call(name)

            time.sleep(random.randint(1, 3))


os.system('cls')
print(BANNER)

try:
    login()
    c = Courses()
    courses = c.get_courses()

    if len(sys.argv)==2:
        course_id = c.select_course(courses)
        monitor_rollcall(courses, course_id)
    else:
        c.print_courses(courses)
        print(f"最小誤差值 : 1秒 && 最大誤差值 : {3*(len(courses)-1)}秒")  #Instant : 1, Max : 3*(len(courses)-1)
        print(f"正在 {len(courses)} 門課程中等待點名...")
        
        while 1:
            monitorCalls(courses)

except KeyboardInterrupt:
    input("\nExited...")

except Exception as e:
    print(str(e.with_traceback()))
    time.sleep(10)
    pass




import paramiko
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from constants import Params

def init():
    connect = paramiko.SSHClient()
    connect.load_system_host_keys()
    connect.connect(Params.SSH_ADDRESS, username=Params.SSH_LOGIN, password=Params.SSH_PASS)
    connect.exec_command("rm test.txt && echo 'hello' >> test.txt")
    connect.close()

class TestClass:

    def setup_class(self):
        init()
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.connect(Params.SSH_ADDRESS, username=Params.SSH_LOGIN, password=Params.SSH_PASS)

    def teardown_class(self):
        self.client.close()

    def test_file(self):
        _, out, _ = self.client.exec_command('cat test.txt')
        assert out.read() == b'hello\n'

    def test_pythonVersion(self):
        _, out, _ = self.client.exec_command('python3 --version')
        assert 'Python 3.' in str(out.read())

    def test_cowSayFiles(self):
        flag = True
        log = ''
        for f in Params.FILES:
            _, out, _ = self.client.exec_command('md5sum ' + f)
            file = str(out.read())[2:-3].split()
            if len(file) == 0:
                flag = False
                log = log + f + ' : does not exist\n'
                continue
            if Params.FILES[f] != file[0]:
                flag = False
                log = log + f + ' : invalid md5sum\n'
        assert flag, log

class TestSelenium:

    def setup(self):
        self.driver = webdriver.Chrome(executable_path=Params.CHROMEDRIVER_EXEC_PATH)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)

    def teardown(self):
        self.driver.close()

    def test_google(self):
        contains = False
        self.driver.get('https://google.com')
        search_field = self.driver.find_element_by_name('q')
        search_field.send_keys('python 3')
        search_field.send_keys(Keys.RETURN)
        for l in self.driver.find_elements_by_css_selector('a[href]'):
            if 'www.python.org' in l.get_attribute('href'):
                contains = True
                break
        assert contains

    def test_kasperskyBrokenLinks(self):
        flag = True
        log = ''
        badcodes = [400, 403, 404, 408, 409, 501, 502, 503]
        self.driver.get('https://kaspersky.com')
        for l in self.driver.find_elements_by_css_selector('a[href]'):
            time.sleep(Params.REQUEST_DELAY)
            try:
                r = requests.get(l.get_attribute("href"), timeout=10)
            except Exception as e:
                if r.status_code in badcodes:
                    flag = False
                    log = log + l.get_attribute("href") + ' : ' + str(r.status_code) + ' status ' + str(e) + '\n'
        assert flag, log

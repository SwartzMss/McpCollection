from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import requests
import json


class OutlookAuthenticator:
    def __init__(self, client_id, client_secret, redirect_uri, scope, username, password):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.username = username
        self.password = password
        self.auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&response_mode=query"
        self.token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

    def authenticate(self):
        driver = webdriver.Chrome()
        driver.get(self.auth_url)

        # 等待页面加载并输入用户名和密码
        time.sleep(5)
        username_input = driver.find_element(By.NAME, "loginfmt")
        username_input.send_keys(self.username)
        username_input.send_keys(Keys.RETURN)
        time.sleep(5)
        password_input = driver.find_element(By.NAME, "passwd")
        password_input.send_keys(self.password)
        password_input.send_keys(Keys.RETURN)
        time.sleep(8)

        # stay_signed_in_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        # stay_signed_in_button.click()
        time.sleep(5)

        #accept_button = driver.find_element(By.XPATH, '//*[@id="idBtn_Accept"]')
        #if accept_button:
        #    accept_button.click()
        time.sleep(5)

        # 获取授权码
        auth_code = driver.current_url.split("code=")[-1].split("&")[0]
        driver.quit()

        return auth_code

    def get_tokens(self, auth_code):
        token_data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }

        response = requests.post(self.token_url, data=token_data)
        tokens = response.json()

        return tokens

    def save_tokens_to_file(self, tokens, file_path):
        with open(file_path, 'w') as file:
            json.dump(tokens, file)


# 使用
client_id = ''
client_secret = ''
redirect_uri = 'https://login.microsoftonline.com/common/oauth2/nativeclient'
scope = 'Mail.ReadBasic Mail.Read Mail.Send Mail.ReadWrite offline_access'
username = 'asas@outlook.com'
password = 'fdfd'

authenticator = OutlookAuthenticator(client_id, client_secret, redirect_uri, scope, username, password)
auth_code = authenticator.authenticate()
tokens = authenticator.get_tokens(auth_code)
authenticator.save_tokens_to_file(tokens, 'tokens.json')

print("令牌已保存到文件")
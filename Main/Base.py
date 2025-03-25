from threading import Thread

# 크롬 설정 베이스
from selenium.webdriver import Chrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

#부가적인 모듈
from selenium.webdriver.support.expected_conditions import presence_of_all_elements_located,presence_of_element_located
from selenium.webdriver.support.expected_conditions import visibility_of_all_elements_located

# docstring
from typing import List,Dict,Callable
import functools

'''
기본적인 크롤링 규칙을 정리해놓은 페이지입니다.
이를 기반으로 과정을 구조화하겠습니다
'''

def __ExceptControl__(func:Callable):
    '''에러 전처리를 위한 데코레이터 함수입니다.'''
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except:
            return None
    return wrapper

@__ExceptControl__
def GetElements(drive:WebElement,condition:str,time_out:int=1,*args,**kwargs):
    '''
    다수의 웹요소 서치
    drive : 기본 웹요소
    condition : Xpath 조건문
    time_out : 동적대기 시간
    '''
    return WebDriverWait(driver=drive,timeout=time_out).until(presence_of_all_elements_located(
        [By.XPATH,condition]))

@__ExceptControl__
def GetElement(drive:WebElement,condition:str,time_out:int=1,*args,**kwargs):
    '''
    단일 웹요소 서치
    drive : 기본 웹요소
    condition : Xpath 조건문
    time_out : 동적대기 시간
    '''
    return WebDriverWait(driver=drive,timeout=time_out).until(presence_of_element_located(
        [By.XPATH,condition]))

def GetDrive(Optional:bool=False):
    '''
    Chrome 작동 전 창을 띄울지 말지에 대해 결정하는 함수입니다.

    Optional=True 일 경우
    창을 띄우지 않습니다
    '''
    chrome_options = Options()
    if Optional:
        chrome_options.add_argument("--headless")  # Headless 모드
    else:
        pass
    return Chrome(options=chrome_options)

def split_standard(webelement:WebElement):
        if ":" in webelement.text:
            return webelement.text.split(":")
        else:
            return webelement.text.split("\n")

def ScrollDown(Bedy:WebElement,Standard:int=0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            while True:
                result=func(*args,**kwargs)
                if len(result)>=Standard:
                    break
                else:
                    Bedy.send_keys(Keys.PAGE_DOWN)
                    continue
            return result
        return wrapper
    return decorator
                


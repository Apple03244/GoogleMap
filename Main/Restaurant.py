from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from typing import List,Dict,Callable
from Base import GetDrive,GetElements,GetElement,split_standard,ScrollDown
import urllib.parse
from functools import wraps


def ParsingURL(search_term:str):
    parsing_term=urllib.parse.quote(search_term)
    return f"https://www.google.co.kr/maps/search/{parsing_term}"

def get_Name_URL(element:WebElement):
    '''레스토랑 이름, URL 수집'''
    ras_name=element.get_attribute("aria-label")
    url=element.get_attribute("href")
    return {"Name":ras_name,"URL":url}

def rating(element:WebElement):
    '''레스토랑 전체 평점'''
    rating_base=GetElement(element,'//*[@role="img"]').get_attribute("aria-label")
    preprocessing=[term for term in rating_base if not term.isalpha()]
    if preprocessing:
        rating="".join([term for term in rating if not term.isalpha()]).strip()
        rating=float(rating)
    else:
        rating=0
    return rating

def category(element:WebElement):
    '''레스토랑 분류'''
    category_base=GetElement(element,"//button[contains(@jsaction,'category')]")
    if category_base:
        return category_base.text
    else:
        return ""

def address(element:WebElement):
    '''레스토랑 주소'''
    address_bass=GetElement(element,
                            '//*[@role="region"]//button[@data-item-id="address"]')
    if address_bass:
        return address_bass.get_attribute("aria-label").replace("주소 :","").strip()
    else:
        return ""
    
def __split_standard__(element:WebElement):
    if ":" in element.text:
        return element.text.split(":")
    else:
        return element.text.split("\n")
    
def get_sub_info(element:WebElement):   
    '''리뷰 중 세부정보 표 정보 정리 후 수집'''      
    sub_infos=GetElements(element,".//div[contains(@jslog,'metadata') and .//span[contains(text(),'')]]")
    result={}
    for sub_info in sub_infos:
        key,value=__split_standard__(sub_info)
        if key in result:
            result[key].append(value)
        else:
            result[key]=[value]
    return result      


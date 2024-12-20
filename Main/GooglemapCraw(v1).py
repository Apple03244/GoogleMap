from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import urllib.parse
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import visibility_of_all_elements_located,presence_of_element_located,presence_of_all_elements_located


class GooglemapCraw():
    def  __init__(self,search_term,craw_num:int,optional:bool=True):

        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Headless 모드

        if optional:
            self.main_drive=Chrome(options=chrome_options) # url까지 크롤
            self.sub_drive=Chrome(options=chrome_options) # 기본정보 크롤
        else:
            self.main_drive=Chrome()
            self.sub_drive=Chrome()
        self.craw_num=craw_num
        self.search_term=search_term
        self.infos=[] # 임시 저장공간

        encoded_text = urllib.parse.quote(self.search_term)
        self.base_path=f"https://www.google.co.kr/maps/search/{encoded_text}" # 크롤링이 될 주소(파싱될 예정)
        pass

    def __restuarant_properties(self,search_term,restaurant_name,url,address,rating,category,**kwrargs):
    
        properties={"검색어" : {"rich_text" : [{"text": {"content": search_term}}]},
                "음식점이름" : {"title" : [{"text" : {'content': restaurant_name}}]},
                "URL" : {"url" : url},
                "주소" : {"rich_text" : [{"text": {"content": address}}]},
                "별점" : {"number" : rating},
                "카테고리" : {"rich_text" : [{"text": {"content": category}}]}
                }
        return properties

    # 리뷰 db insert 기초 틀
    def __review_properties(self,restaurant_name,user,review,**kwargs):

        properties={"음식점이름" : {"title" : [{"text": {"content": restaurant_name}}]},
                    "유저" : {"rich_text" : [{"text": {"content": user}}]},
                    "리뷰" : {"rich_text" : [{"text": {"content": review}}]}
                    }
        return properties
    
    def craw_restaurant(self):
        self.main_drive.get(self.base_path)
        # 스크롤을 내리는 공간
        main_box=WebDriverWait(self.main_drive,3).until(
        presence_of_element_located([By.XPATH, '//*[@role="feed"]']))

        while True:
            main_box.send_keys(Keys.PAGE_DOWN)

            feed_box=WebDriverWait(self.main_drive,3).until(
                visibility_of_all_elements_located([By.CSS_SELECTOR,"a.hfpxzc"]))
            
            if len(feed_box)>self.craw_num:
                break
        
        for sub_feed in feed_box:
            #음식점 이름
            restaurant_name=sub_feed.get_attribute("aria-label")
            url=sub_feed.get_attribute("href")

            self.infos.append(
                {"search_term":self.search_term,
                 "restaurant_name":restaurant_name,
                 "url":url}
            )

        for sub_info in self.infos:
            self.sub_drive.get(sub_info["url"])

            #별점
            rating=WebDriverWait(self.sub_drive,3).until(
            presence_of_element_located([By.XPATH, '//*[@role="img"]'])).get_attribute("aria-label")
            #전처리
            rating="".join([term for term in rating if not term.isalpha()]).strip()
            rating=float(rating)

            #음식점 카테고리
            category=WebDriverWait(self.sub_drive,3).until(
            presence_of_element_located([By.CSS_SELECTOR,'button.DkEaL'])).text

            #정보선택칸
            tabs=WebDriverWait(self.sub_drive,3).until(
            presence_of_all_elements_located([By.XPATH, '//*[@role="tab"]']))
            tab_select={element.text:element for element in tabs} # 이후 사용할 예정
            
            #하위 정보칸
            info_region=WebDriverWait(self.sub_drive,3).until(
            presence_of_element_located([By.XPATH, '//*[@role="region"]']))
            #주소
            address=WebDriverWait(info_region,3).until(
            presence_of_element_located([By.XPATH, '//*[@data-item-id="address"]'])).text

            sub_info.update(
                {"address":address,
                 "rating":rating,
                 "category":category}
            )
    def close(self):
        self.main_drive.quit()
        self.sub_drive.quit()

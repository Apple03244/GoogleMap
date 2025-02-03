from selenium.webdriver import Chrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import urllib.parse
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import visibility_of_all_elements_located,presence_of_element_located,presence_of_all_elements_located
from threading import Thread
from typing import List,Dict
from tqdm import tqdm

class GooglemapCraw():
    def  __init__(self,search_term,restaurant_num:int,review_num:int=100,thread_num:int=1,optional:bool=True):

        # Chrome 옵션 설정
        self.chrome_options = Options()
        if optional:
            self.chrome_options.add_argument("--headless")  # Headless 모드
        else:
            pass

        self.main_drive=Chrome(options=self.chrome_options) # url까지 크롤
        self.restaurant_num=restaurant_num
        self.search_term=search_term
        self.infos=[] # 레스토랑 저장공간
        self.reviews=[] #리뷰 저장공간
        self.thread_num=thread_num
        self.review_num=review_num

        encoded_text = urllib.parse.quote(self.search_term)
        self.base_path=f"https://www.google.co.kr/maps/search/{encoded_text}" # 크롤링이 될 주소(파싱될 예정)
        pass

    # 멀티 스래딩 적용 
    def __crawras(self,sub_info_list:List[Dict],**kwargs):
        sub_drive=Chrome(options=self.chrome_options)
        for sub_info in sub_info_list:
            sub_drive.get(sub_info["url"])

            #별점
            rating=WebDriverWait(sub_drive,3).until(
            presence_of_element_located([By.XPATH, '//*[@role="img"]'])).get_attribute("aria-label")
            #전처리
            rating="".join([term for term in rating if not term.isalpha()]).strip()
            rating=float(rating)

            #음식점 카테고리
            category=WebDriverWait(sub_drive,3).until(
            presence_of_element_located([By.XPATH,"//button[contains(@jsaction,'category')]"])).text
            
            #하위 정보칸
            info_region=WebDriverWait(sub_drive,3).until(
            presence_of_element_located([By.XPATH, '//*[@role="region"]']))
            #주소
            address=WebDriverWait(info_region,3).until(
            presence_of_element_located([By.XPATH,'//button[@data-item-id="address"]'])).get_attribute("aria-label").replace("주소 :","").strip()

            sub_info.update(
                {"address":address,
                "rating":rating,
                "category":category}
            )
        sub_drive.quit()
    
    # 구글 리뷰 선택 평가(표의 형태로 변동성이 큰 리뷰 틀)
    def __subrevtable(self,sub_review:WebElement):
        splited_table={}
        try:
            reviewer_table=WebDriverWait(sub_review,1).until(
                    presence_of_all_elements_located([By.XPATH,".//div[@jslog]/div[contains(@jslog,'metadata')]"]))
            #구분자 설정
            def spliter(text:str):
                split_txt="\n" if "\n" in text else ":"
                return text.split(split_txt)
            for row in reviewer_table:
                splited_table.update({key:value for key,value in [spliter(row.text)]})
            
        except:
            pass

        return splited_table


    # 리뷰 크롤링 작업
    def __crawrev(self,sub_info_list:List[Dict],**kwargs):
        sub_drive=Chrome(options=self.chrome_options)
        for sub_info in sub_info_list:
            sub_drive.get(sub_info["url"])

            #정보선택칸
            tabs=WebDriverWait(sub_drive,3).until(
            presence_of_all_elements_located([By.XPATH, '//button[@role="tab"]']))
            tab_select={element.text.strip():element for element in tabs} 

            #리뷰 크롤링
            tab_select["리뷰"].click() #리뷰창으로 전환

            #현재 리뷰 개수
            total_review_num=WebDriverWait(sub_drive,3).until(
            presence_of_element_located([By.XPATH,"//div[contains(text(), '리뷰') and contains(@jslog,'metadata')]"])).text
            #전처리
            total_review_num=int("".join([term for term in total_review_num if term.isnumeric()]))

            #스크롤가능한 바디찾기
            candidate_list=WebDriverWait(sub_drive,3).until(
                 presence_of_all_elements_located([By.XPATH,"//div[contains(@jslog,'mutable')]"]))
            try:
                scroll_body=[element for element in candidate_list 
                         if any(["auto" in element.value_of_css_property("overflow"),
                                 "scroll" in element.value_of_css_property("overflow")])][0]
            
                while True: 
                    scroll_body.send_keys(Keys.PAGE_DOWN)

                    #리뷰 각각의 객체
                    review_box=WebDriverWait(sub_drive,3).until(
                        presence_of_all_elements_located([By.XPATH
                        ,"//div[@data-review-id and contains(@jsaction,'review.out')]"])) 

                    if (len(review_box)==total_review_num)or(len(review_box)>self.review_num):
                        break
            except:
                review_box=WebDriverWait(sub_drive,3).until(
                        presence_of_all_elements_located([By.XPATH
                        ,"//div[@data-review-id and contains(@jsaction,'review.out')]"]))
            # 리뷰 돌아가며 더보기 누르기(공통 작업)
            for sub_review in review_box:
                base_dict=sub_info.copy()
                sub_drive.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", sub_review)

                try:
                    button=WebDriverWait(sub_review,2).until(
                    presence_of_element_located([By.XPATH,".//button[contains(text(),'자세히')]"]))
                    button.click()
                except: # 리뷰가 짧으면 없음
                    pass

                #리뷰 유저 정보(이름, 주소)
                reviewer_info=WebDriverWait(sub_review,3).until(
                    presence_of_element_located([By.XPATH,".//button[@aria-label and contains(@jsaction,'reviewerLink')]"]))
                
                reviewer_name=reviewer_info.get_attribute("aria-label").replace("사진","")
                reviewer_href=reviewer_info.get_attribute("data-href")

                # 총합 별점
                reviewer_total_rating=WebDriverWait(sub_review,3).until(
                    presence_of_element_located([By.XPATH
                    ,".//span[@role='img' and contains(@aria-label,'별표')]"])).get_attribute("aria-label")
                reviewer_total_rating=float("".join([temp for temp in reviewer_total_rating if not temp.isalpha()]))

                #리뷰 본문
                reviewer_rev=WebDriverWait(sub_review,3).until(
                    presence_of_element_located([By.XPATH,".//div[@lang='ko']/span[not(@jslog)]"])).text

                #하위 리뷰 table 구조화
                rev_sub_table=self.__subrevtable(sub_review)

                base_dict.update(
                    {"user":reviewer_name,
                     "user_url":reviewer_href,
                     "review_total_rate":reviewer_total_rating,
                     "review_text":reviewer_rev,}
                )
                base_dict.update(rev_sub_table)

                self.reviews.append(base_dict)
                        
        sub_drive.quit()
        #return sub_info
    
    def craw_ras(self): # 기초정보 수집 -> 1개의 스래딩으로 충분
        self.main_drive.get(self.base_path)
        # 스크롤을 내리는 공간
        main_box=WebDriverWait(self.main_drive,3).until(
        presence_of_element_located([By.XPATH, '//*[@role="feed"]']))

        while True:
            main_box.send_keys(Keys.PAGE_DOWN)

            feed_box=WebDriverWait(self.main_drive,3).until(
                 presence_of_all_elements_located([By.XPATH,"//a[@href and @aria-label]"]))
            

            if len(feed_box)>self.restaurant_num:
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

        self.main_drive.quit()

        thread_list4ras=[]
        m=len(self.infos)//self.thread_num
        for n in range(self.thread_num):
            kw=self.infos[n*m:(n+1)*m]
            sub_thread4ras=Thread(target=self.__crawras,kwargs=({"sub_info_list":kw}))
            thread_list4ras.append(sub_thread4ras)
            sub_thread4ras.start()        
                
        for sub_thread in tqdm(thread_list4ras):
            sub_thread.join()

    def craw_rev(self):
        thread_list4rev=[]
        m=len(self.infos)//self.thread_num
        for n in range(self.thread_num):
            kw=self.infos[n*m:(n+1)*m]
            sub_thread4rev=Thread(target=self.__crawrev,kwargs=({"sub_info_list":kw}))
            thread_list4rev.append(sub_thread4rev)
            sub_thread4rev.start()

        for sub_thread in tqdm(thread_list4rev):
            sub_thread.join()


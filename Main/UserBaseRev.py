from selenium.webdriver import Chrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from typing import List,Dict
from selenium.webdriver.support.expected_conditions import visibility_of_all_elements_located,presence_of_element_located,presence_of_all_elements_located
from threading import Thread
from tqdm import tqdm

class UserBaseRev:
    def __init__(self,review_num:int=100,thread_num:int=1,optional:bool=True,*args):
        self.chrome_options = Options()
        if optional:
            self.chrome_options.add_argument("--headless")  # Headless 모드
        else:
            pass

        #self.main_drive=Chrome(options=self.chrome_options) # url까지 크롤
        self.infos=[] # 레스토랑 저장공간
        self.reviews=[] #리뷰 저장공간
        self.thread_num=thread_num
        self.review_num=review_num
        self.drivelist=[]

        for _ in range(thread_num):
            sub_drive=Chrome(options=self.chrome_options)
            self.drivelist.append(sub_drive)

        pass
    
    def __get_rev_num__(self,drive:Chrome):
        try:
            review_num=WebDriverWait(drive,3).until(presence_of_element_located
                    ([By.XPATH,"//span[contains(text(),'리뷰') and contains(text(),'개')]"]))
            text_box=review_num.text.split(" ")
            
            text_box=review_num.text.split(" ")
            for i in range(len(text_box)):
                                if "리뷰" in text_box[i]:
                                    _idx_=i
                                    break

            num=int("".join([text for text in text_box[_idx_+1] if text.isdigit()]))
            search_num=self.review_num if self.review_num<=num else num
            return search_num
        except:
            return 0
        
    def __remove_moreinfo__(self,webelements:List[Chrome],temp_num:int=0):
        for webelement in webelements[temp_num:]:
            try:
                button=WebDriverWait(webelement,1).until(presence_of_element_located(
                    (By.XPATH,".//button[contains(text(),'자세히') and @aria-label='더보기']")))
                button.click()
            except:
                continue
        return webelements,len(webelements)
    
    def __split_standard__(self,webelement:Chrome):
         if ":" in webelement.text:
              return webelement.text.split(":")
         else:
              return webelement.text.split("\n")
         

    def __get_sub_info__(self,webelement:Chrome):         
        #def get_sub_info(webelement:Chrome,sub_info_title:str):
        try:
            sub_infos=WebDriverWait(webelement,1).until(
            presence_of_all_elements_located([By.XPATH,f".//div[contains(@jslog,'metadata') and .//span[contains(text(),'')]]"]))
            splited_text=[self.__split_standard__(sub_info) for sub_info in sub_infos]
            
            result={}   
            for sub_info in sub_infos:
                key,value=self.__split_standard__(sub_info)
                if key in result:
                    result[key].append(value)
                else:
                    result[key]=[value]
            return result      
        except:
            return {} 

    def __get_info__(self,webelement:Chrome):
        title=WebDriverWait(webelement,1).until(
              presence_of_element_located([By.XPATH,".//div[contains(@style,'position: relative;')]"])
        ).text
        restaurant_name,restaurant_location=title.split("\n")

        stars=WebDriverWait(webelement,1).until(
              presence_of_element_located([By.XPATH,".//span[@role='img' and contains(@aria-label,'별표')]"])
         ).get_attribute("aria-label")
        stars="".join([num_txt for num_txt in stars if num_txt.isdigit()])

        main_review=WebDriverWait(webelement,1).until(
              presence_of_element_located([By.XPATH,".//div[@tabindex and @id]/span"])).text
        
        base_result= {'restaurant_name': restaurant_name,
                'restaurant_location' : restaurant_location,
                'stars' : stars,
                'main_review' :  main_review}
        
        base_result.update(
             self.__get_sub_info__(webelement)
        )
        return base_result
        
        
    def __crawrev(self,drive:Chrome,user_url:str,**kwargs):
        drive.get(user_url)

        rev_table=WebDriverWait(drive,2).until(presence_of_element_located(
            [By.XPATH,"//div[@role='tabpanel']"]
        ))
        
        use_rev_num=self.__get_rev_num__(drive)
        
        # 리뷰가 없음, 리뷰가 있으나 확인할 수 없는 경우 방지
        if not use_rev_num:
            return {}
        else:
            pass

        # 내부의 '자세히' 제거 및 스크롤 다운
        sub_rev_table=WebDriverWait(rev_table,2).until(presence_of_all_elements_located(
        [By.XPATH,".//div[contains(@jsaction,'review.open') and @role='button']"]))
        
        sub_rev_table,sub_search_num=self.__remove_moreinfo__(sub_rev_table,0)

        while True:
            if sub_search_num<use_rev_num:

                drive.execute_script("arguments[0].scrollIntoView();",sub_rev_table[-1])
                
                while True:
                    try:
                        ckpoint=WebDriverWait(rev_table,1).until(
                        lambda driver: len(driver.find_elements(
                        By.XPATH,".//div[contains(@jsaction,'review.open') and @role='button']"))>sub_search_num)
                        break
                    except: 
                        rev_table.send_keys(Keys.DOWN)

                sub_rev_table=WebDriverWait(rev_table,2).until(presence_of_all_elements_located(
                [By.XPATH,".//div[contains(@jsaction,'review.open') and @role='button']"]))
                sub_rev_table,sub_search_num=self.__remove_moreinfo__(sub_rev_table,sub_search_num)
            else:
                break
        #return sub_rev_table
        craw_result=[]
        for table in sub_rev_table:
             craw_result.append(self.__get_info__(table))
        return craw_result
    
    def crawreview(self,url_list:List[str],thread_num:int):
        thread_list=[]
        n=len(url_list)//thread_num

        for i in range(thread_num):
            url_lst=[url[i*n:(i+1)] for url in url_list]
            sub_thread=Thread(target=lambda urls : [self.__crawrev(url) for url in urls],kwargs={"urls":url_lst})
            thread_list.append(sub_thread)
            sub_thread.start()

        for thread in thread_list:
            thread.join()


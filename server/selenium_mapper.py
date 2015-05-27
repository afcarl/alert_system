import time
from datetime import datetime
import random
import os
from unidecode import unidecode
import hashlib
import shutil
import ssl
from selenium import webdriver

"""
Functions for the user:
map_images(base_url,depth): Gets the links for all the images on a given set of web pages
map_pdfs(url,depth): Gets the links for all the pdfs on a given set of web pages
map_links(base_url,depth): Gets all the links for all the pages of a given website, upto a certain depth.
Recommended depth: 3 - 6 (otherwise request may time out)
"""

#reference: http://stackoverflow.com/questions/16604162/selenium-download-full-html-page

class Mapper:
    def __init__(self,base=None):
        self.base = base
        self.dir_base = base.split(".")[1]
        self.nav_base = "http://localhost:5000/" #this will need to change
        self.driver = webdriver.PhantomJS()
        
    #ToDo Image_save
    def image_save(self,img_src,file_name):
        print "saving image:"+img_src
        img_dir = "images"+file_name
        if not os.path.exists(img_dir):
            os.mkdir(img_dir)
        os.chdir(img_dir)
        path = img_src.split("/")[-1].replace(".","_").replace("?","_").replace("&","_").replace("=","_").replace("+","_").replace(":","_").replace("-","")
        try:
            r = requests.get(img_src, stream=True)
        except:
            return
        if r.status_code == 200:
            with open(path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)  
                m_md5 = hashlib.md5()
                m_sha = hashlib.sha256()
                m_sha.update(str(r.raw))
                m_md5.update(str(r.raw))
                with open("sha_img_hashes.txt","a") as h:
                    h.write(str(datetime.now())+path+":"+m_sha.hexdigest()+"\n")
                with open("md5_img_hashes.txt","a") as f:
                    f.write(str(datetime.now())+path+":"+m_md5.hexdigest()+"\n")
        os.chdir("../")

    #ToDo: Storage
    def storing(self,links):
        print "storing started"
        print len(links)
        responses = []
        original_dir = self.dir_base+"_"+datetime.now().strftime("%Y%m%d_%H%M")
        if not os.path.exists(original_dir):
            os.mkdir(original_dir)
        os.chdir(original_dir)
        hashes = []
        for link in links:
            self.driver.get(link)
            time.sleep(2)
            text = unidecode(self.driver.page_source)
            imgs = self.image_grab(link)
            m_sha = hashlib.sha256()
            m_md5 = hashlib.md5()
            fixed_url = link.replace(".","_").replace("?","_").replace("&","_").replace("=","_").replace("+","_").replace(":","_").replace("-","")
            file_name = "_".join(fixed_url.split("/")[-3:-1])+"_"+fixed_url.split("/")[-1]
            for img in imgs: self.image_save(img,file_name)
            m_sha.update(text)
            m_md5.update(text)
            with open(file_name,"w") as f:
                #print file_name
                f.write(text)
            with open("sha_hashes.txt","a") as h:
                h.write(str(datetime.now())+file_name+":"+m_sha.hexdigest()+"\n")
            with open("md5_hashes.txt","a") as f:
                f.write(str(datetime.now())+original_dir+file_name+":"+m_md5.hexdigest()+"\n")
        os.chdir("../")

    def link_grab(self,url):
        """Returns all links on the page.  
        Aka all those links who include the base url in the link."""
        links = []
        try:
            self.driver.get(url)
        except:
            return []
        potential_links = [l.get_attribute("href") for l in self.driver.find_elements_by_xpath("//a")]
        
        if None in potential_links:
            while None in potential_links:
                potential_links.remove(None)
        
        for link in potential_links:
            print link
            if self.base in link:
                links.append(link)
            else:
                if link.startswith("http"):
                    links.append(link)
                elif self.base.endswith("/"):
                    if link.startswith("/"):
                        link = link.lstrip("/")
                        link = self.base + link
                    else:
                        link = self.base + link
                    links.append(link)
        return links

    def map_links(self,url,depth):
        link_list = []
        return mapper(url,depth,link_list)

    def mapper(self,url,depth,link_list):
        """Grabs all the links on a given set of pages, does this recursively."""
        if depth <= 0:
            return link_list
        links_on_page = self.link_grab(url)
        tmp = []
        for link in links_on_page:
            if not link in link_list:
                link_list.append(link)
                tmp = self.mapper(link,depth-1,link_list)
                for elem in tmp:
                    if not elem in link_list:
                        link_list.append(elem)
        return link_list

    def map_pdfs(self,url,depth):
        """Grabs all the pdfs on a given set of pages."""
        links = self.map_website(url,depth)
        pdfs = []
        for link in links:
            if ".pdf" in link:
                pdfs.append(link)
        return pdfs

    def image_grab(self,url):
        """Returns all images on the page."""        
        self.driver.get(url)
        imgs = []
        for img in [i.get_attribute("src") for i in self.driver.find_elements_by_xpath("//img")]:
            if "http" in img:
                imgs.append(img)
            else:
                imgs.append(self.base+img)
        return imgs
                        
#potential issue and fix: http://stackoverflow.com/questions/14102416/python-requests-requests-exceptions-sslerror-errno-8-ssl-c504-eof-occurred
if __name__ == "__main__":
    print "mapping stuff"
    m = Mapper("http://www.tropicaladultvacations.net/")
    links = m.mapper("http://www.tropicaladultvacations.net/",4,[])
    print "storing stuff"
    cur_dir = os.getcwd()
    os.chdir("../storage")
    m.storing(links)
    os.chdir(cur_dir)

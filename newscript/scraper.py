from bs4 import BeautifulSoup
import csv
from selenium import webdriver
import time
import os


options = webdriver.ChromeOptions()
options.add_argument('headless') # Избавляемся от открытия браузера.
driver = webdriver.Chrome(executable_path="chromedriver.exe", service_log_path=os.devnull, options=options) # Подключаем опцию для того, чтобы не открывать браузер и не выводить log файл selenium
driver.get("http://www.st-petersburg.vybory.izbirkom.ru/st-petersburg/ik_r/") # Открываем главную страницу
time.sleep(3)

all_tiks = driver.find_elements_by_xpath("/html/body/div[1]/div[1]/div[3]/div[2]/div[1]/div/ul/li/ul/li/a") # Получаем все ТИК
for i in range(len(all_tiks)):
    all_tiks = driver.find_elements_by_xpath("/html/body/div[1]/div[1]/div[3]/div[2]/div[1]/div/ul/li/ul/li/a")
    name_of_tik = all_tiks[i].text
    all_tiks[i].click()
    time.sleep(1)
    all_uiks = driver.find_elements_by_xpath("/html/body/div[1]/div[1]/div[3]/div[2]/div[1]/div/ul/li/ul/li/ul/li/a") # Получаем все УИК
    all_uiks_names = []
    for uik in all_uiks:
        all_uiks_names.append(uik.text)
    for uik_name in all_uiks_names:
        index_for_page_start = uik_name.find("№")
        number_element_from_page = uik_name[index_for_page_start+1:].strip()
        driver.get(f"http://www.st-petersburg.vybory.izbirkom.ru/st-petersburg/ik_r/{number_element_from_page}") # Проходим по каждой ссылке
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "lxml")
        trs = soup.find("div", class_="table margtab").find_all("tr")[2:] # Собираем все данные о Физ лицах
        for tr in trs:
            tds = tr.find_all("td")
            with open("output.tsv", "a+", newline="", encoding='UTF8') as out_file: # Запись в tsv файл
                tsv_writer = csv.writer(out_file, delimiter="\t", escapechar='\t', quoting=csv.QUOTE_NONE)
                tsv_writer.writerow(["Санкт-Петербургская избирательная комиссия", name_of_tik, uik_name, tds[1].get_text(), tds[2].get_text(), tds[3].get_text()])
driver.quit()
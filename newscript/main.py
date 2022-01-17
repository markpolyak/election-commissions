import requests as rq
from bs4 import BeautifulSoup
import csv
HOST =  "http://www.st-petersburg.vybory.izbirkom.ru/st-petersburg"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'        
}
URL_API = "http://www.st-petersburg.vybory.izbirkom.ru/st-petersburg/ik_r_tree/{}?first=1&id2={}"
def get_html(url):
    return rq.get(url, headers=HEADERS).content
def get_json(url):
    return rq.get(url, headers=HEADERS).json()
def get_soup(url):
    return BeautifulSoup(get_html(url), 'html.parser')
def parse_table(uik, father_name, father2_name, child_name, tsv_writer):
    url = HOST + "/ik_r/" + str(uik)
    soup = get_soup(url)
    table = soup.find("div", class_="table margtab")
    lines = table.findAll("tr")
    for line in lines:
        cells = line.findAll("td")
        if(len(cells)==4):
            name = cells[1].text
            status = cells[2].text
            organ = cells[3].text
            tsv_writer.writerow([father_name, father2_name + " " + child_name, name.strip(), status, organ])
with open('output.tsv', 'wt') as out_file:
    tsv_writer = csv.writer(out_file, delimiter='\t')
    father1  = get_json(URL_API.format("278200090968", "278200090968"))[0]
    father_name = father1["text"]
    for father2 in father1["children"]:
        father2_name = father2["text"] 
        father2_id = father2["id"]
        url_father2 = HOST + r"/ik_r_tree/?id="+father2_id
        childrens = get_json(url_father2)
        for children in childrens:
            parse_table(children["id"], father_name, father2_name, children["text"], tsv_writer)
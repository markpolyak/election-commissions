
#from geocoder import Batch
#service = Batch(apikey="ea6GxYtD4_ArYWL2FPAGcuW0YbDohQkPA8bEajbgGqA")
#service.start("kolvo.tsv", indelim=";", outdelim=";")


import requests
import json
import time
import zipfile
import io
from bs4 import BeautifulSoup
completed=0

def step1():
    file = open('commissions.tsv', 'r',encoding='ansi')   
    my_file = open("testing1.tsv", "w",encoding='ansi')
    my_file.write("recId\tsearchText\n")
    a=1
    #c = sum(1 for line in file)
 
    lines = file.readlines()
    for line in lines:
      if(a==1):
        a+=1
        continue
      partitioned_string = line.partition('\t')
      my_file.write(str(a-1)+"\t")
      my_file.write(partitioned_string[0]+"\n")
      a+=1
    file.close()
    my_file.close()

def step2():
    x=3
    counter = 0
    my_file1 = open("testing1.tsv", "r",encoding='ansi')
    my_file2 = open("testing2.tsv", "w",encoding='utf-8')
   # my_file2.write("   recId; searchText")
    lines = my_file1.readlines()
    signal=0
    signal2=0
    for line in lines:
     
      a=len(line)
      b = line.count(',')
      if (x>0):  
          my_file2.write(line)
          x=x-1
          continue

      for i in range (a):
        if (line[i] ==","): counter+=1
        if (counter == 3 and i+5<=a):
          if(line[i+2] == 'м' and line[i+3] == 'у' and line[i+4] == 'н' and line[i+5] == 'и'):
            signal = 1
        if (counter == 4):
          signal = 0
        if (counter == 4 and i+5<a):
            if (line[i+2] == 'м' and line[i+3] == 'у' and line[i+4] == 'н' and line[i+5] == 'и'):
                signal2=1
        if (counter == 5):
          signal2 = 0
        if (counter == b):
          continue
        if (signal == 0 and signal2==0):
          my_file2.write(line[i])
      my_file2.write("\n")
      counter=0

    my_file1.close()
    my_file2.close()
def step3():

    service = Batch(apikey="vyWu2e2gI2pl0pAG2d-tYkrheID7ALAvjfpC2sIe_AQ")
    service.start("testing2.tsv", indelim="\t", outdelim="\t")
    while(True):
        print ("Для проверки статуса введите 1\nДля получения файла введите 2")
        a=input()
        if (a=="1"):
            service.status()
            time.sleep(1)
        else:
            service.result()
            break
    print ("Введите название полученного файла:")
    a=input()
    file = open(a, 'r', encoding='utf-8')   
    my_file = open("result.tsv", "w",encoding='utf-8')
    my_file.write("displayLatitude\tdisplayLongitude\tlocationLabel\n")
    a=1
    signal=0
    #c = sum(1 for line in file)
    counter = 0  
    lines = file.readlines()
    for line in lines:

      if(a==1):
        a+=1
        continue

      partitioned_string = line.partition('\t')
      temp_string=partitioned_string[2]
      partitioned_string = temp_string.partition('\t')
      temp_string=partitioned_string[2]
      partitioned_string = temp_string.partition('\t')
      temp_string=partitioned_string[2]


      partitioned_string = temp_string.partition('\t')
      temp_string=partitioned_string[2]

      my_file.write(partitioned_string[0])
      my_file.write("\t")
      partitioned_string = temp_string.partition('\t')
      temp_string=partitioned_string[2]

      my_file.write(partitioned_string[0])
      my_file.write("\t")
      partitioned_string = temp_string.partition('\t')
      my_file.write(partitioned_string[0])
      my_file.write("\t")
      my_file.write("\n")
    file.close()
    my_file.close()

class Batch:

    SERVICE_URL = "https://batch.geocoder.ls.hereapi.com/6.2/jobs"
    jobId = None

    def __init__(self, apikey="vyWu2e2gI2pl0pAG2d-tYkrheID7ALAvjfpC2sIe_AQ"):
        self.apikey = apikey
        
            
    def start(self, filename, indelim="\t", outdelim="\t"):
        
        file = open(filename, 'rb')

        params = {
            "action": "run",
            "apiKey": self.apikey,
            "politicalview":"RUS",
            "gen": 9,
            "maxresults": "1",
            "header": "true",
            "indelim": indelim,
            "outdelim": outdelim,
            "outcols": "displayLatitude,displayLongitude,locationLabel,houseNumber,street,district,city,postalCode,county,state,country",
            "outputcombined": "true",
        }

        response = requests.post(self.SERVICE_URL, params=params, data=file)
        self.__stats (response)
        file.close()
    

    def status (self, jobId = None):

        if jobId is not None:
            self.jobId = jobId
        
        statusUrl = self.SERVICE_URL + "/" + self.jobId
        
        params = {
            "action": "status",
            "apiKey": self.apikey,
        }
        
        response = requests.get(statusUrl, params=params)
        self.__stats (response)
        

    def result (self, jobId = None):

        if jobId is not None:
            self.jobId = jobId
        
        print("Requesting result data ...")
        
        resultUrl = self.SERVICE_URL + "/" + self.jobId + "/result"
        
        params = {
            "apiKey": self.apikey
        }
        
        response = requests.get(resultUrl, params=params, stream=True)
        
        if (response.ok):    
            zipResult = zipfile.ZipFile(io.BytesIO(response.content))
            zipResult.extractall()
            print("File saved successfully")
        
        else:
            print("Error")
            print(response.text)
    

    
    def __stats (self, response):
        if (response.ok):
            parsedXMLResponse = BeautifulSoup(response.text, "lxml")

            self.jobId = parsedXMLResponse.find('requestid').get_text()
            
            for stat in parsedXMLResponse.find('response').findChildren():
                if(len(stat.findChildren()) == 0):
                    print("{name}: {data}".format(name=stat.name, data=stat.get_text()))

        else:
            print(response.text)


def main():

 step1()
 step2()
 step3()


if __name__ == "__main__":
 main()
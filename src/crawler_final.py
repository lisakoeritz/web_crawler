import requests
import pprint
import re
import time
import math
import nltk
import string
import csv
import json
from nltk.stem.snowball import GermanStemmer
from nltk.stem import SnowballStemmer
from nltk import word_tokenize
from bs4 import BeautifulSoup

counter = 0
log = set()
tokenlist = []
tokenlistGlobal = []
urllist = []
frequencylist = []
idflist = []
tfidflist = []
frequencyAbs = {}
globalfrequencyAbs = []
totalInvList = {}
totalIndex = {}
start_url = 'http://www.datenlabor.berlin'
urls = '/Users/lisaruth/Desktop/CMTS_BOOTCAMP/urls.log'
content = '/Users/lisaruth/Desktop/CMTS_BOOTCAMP/content.csv'
stopword_file = '/Users/lisaruth/Desktop/CMTS_BOOTCAMP/stopwords.csv'
uniqueTokens = '/Users/lisaruth/Desktop/CMTS_BOOTCAMP/uniqueTokenFile.csv'
invIndex_file = '/Users/lisaruth/Desktop/CMTS_BOOTCAMP/invIndex_file.json'
stopword_file = '/Users/lisaruth/Desktop/CMTS_BOOTCAMP/stopwords.csv'

#spider crawls subpages of the website, calls method to extract tokens and saves urls in log
def spider(url):
    if not start_url in log:
        log.add(start_url)
    global counter
    counter += 1
    source_code = requests.get(url, allow_redirects=True)
    # just get the code, no headers or anything
    plain_text = source_code.text
    # BeautifulSoup objects can be sorted through easy
    soup_links = BeautifulSoup(plain_text,'html.parser')
    #get tokens from document
    get_tokens(plain_text, url)

    for link in soup_links.findAll('a', href = re.compile(r'^[^http].*[\.html|\.php\?id=\d{1,2}]$')):
        href = "http://www.datenlabor-berlin.de/" + link.get('href')
        if requests.get(href).status_code == 200:
            if not href in log:
                log.add(href)
                save_log(href)
                spider(href)

def get_tokens(plain_text, url):
    soup = BeautifulSoup(plain_text,'html.parser')
    # kill all script and style elements
    for script in soup(["script", "style", "footer", "header"]):
        script.extract()    # rip it out
    # get text
    text = soup.get_text()
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    #tokenize content
    tokenlist = word_tokenize(text)
    #clean list of tokens
    tokenlist = sanitize(tokenlist)
    #ENTWEDER
    #[tokenlist.remove(token) for token in tokenlist if not re.match(r'\w(\w|\-|\/|\.)*\w',token)]
    #ODER
    matchlist = []
    [matchlist.append(token) for token in tokenlist if re.match(r'\w(\w|\-|\/|\.)*\w',token)]
    tokenlist = delete_stopwords(matchlist)

    tokenProcessing(tokenlist, url)

def tokenProcessing(tokenlist, url):
    tokenlistUnique = []
    for token in tokenlist:
        frequency = tokenlist.count(token)
        if not token in tokenlistUnique:
            frequencylist.append(frequency)
            absDocFrequency(token, frequency)
            urllist.append(url)
            tokenlistUnique.append(token)
    tokenlistGlobal.extend(tokenlistUnique)
    totalInvList[url] = file_index(tokenlist)

def file_index(tokenlist):
    invIndex = {}
    for pos, token in enumerate(tokenlist):
        if token in invIndex.keys():
            invIndex[token].append(pos)
        else:
            invIndex[token] = [pos]
    return invIndex

def fullIndex(url_index_dic):
	total_index = {}
	for url in url_index_dic.keys():
		for token in url_index_dic[url].keys():
			if token in total_index.keys():
				if url in total_index[token].keys():
					total_index[token][url].extend(url_index_dic[url][token][:])
				else:
					total_index[token][url] = url_index_dic[url][token]
			else:
				total_index[token] = {url: url_index_dic[url][token]}
	return total_index

def write_index_to_JSON():
    totalIndex = fullIndex(totalInvList)
    with open(invIndex_file, 'w') as indexfile:
        json.dump(totalIndex,indexfile)
    indexfile.close

def idf():
    print(counter)
    for token in tokenlistGlobal:
        x = counter / tokenlistGlobal.count(token)
        idf = math.log10(x)
        idflist.append(idf)

def tf_idf():
    for index, token in enumerate(tokenlistGlobal):
        tfidf = frequencylist[index] * idflist[index]
        tfidflist.append(tfidf)

def absDocFrequency(token, frequency):
    if token in frequencyAbs.keys():
        frequencyAbs[token][0] += frequency
    else:
        frequencyAbs[token] = [frequency]

def globalAbsFrequency():
    for token in tokenlistGlobal:
        if token in frequencyAbs.keys():
            globalfrequencyAbs.append(frequencyAbs[token][0])

def save_log(url):
    file.write("%s: %s\n" % (time.strftime("%d.%m.%Y %H:%M:%S"), url))

def sanitize(wordList):
    wordList = [re.sub("\xad","", word) for word in wordList]
    wordList = [word.lower() for word in wordList]
    return wordList

def delete_stopwords(tokenlist):
    stopwords = ['']
    filteredlist = []
    with open(stopword_file,'rt') as f:
        wordlist = csv.reader(f)
        for stopword in wordlist:
            stopwords.append(stopword[0])
    for token in tokenlist:
        if not token in stopwords:
            filteredlist.append(token)
    return filteredlist

def write_to_file():
    with open(content,'w') as f:
        csv.excel.delimiter='   '
        f.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format("URL", "token", "Häufigkeit p. Dok.", "tf", "idf", "tf-idf"))
        printlist = (sorted(zip(urllist, tokenlistGlobal, frequencylist, globalfrequencyAbs, idflist, tfidflist), key=lambda x: x[3], reverse=True))
        for x in printlist:
            f.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(*x))

def write_to_uniqueTokenFile():
    uniqueTokenlistGlobal = []
    uniqueTokenFile = open(uniqueTokens, 'w')
    wr = csv.writer(uniqueTokenFile, dialect='excel-tab')
    stemmer = SnowballStemmer("german")
    for token in tokenlistGlobal:
        if token not in uniqueTokenlistGlobal:
            uniqueTokenlistGlobal.append(token)
            stemmedToken = stemmer.stem(token)
            wr.writerow([token, stemmedToken])
    uniqueTokenFile.close

if __name__ == "__main__":
    file = open(urls, "a")
    spider(start_url)
    idf()
    tf_idf()
    globalAbsFrequency()
    write_to_file()
    write_to_uniqueTokenFile()
    write_index_to_JSON()
    file.close

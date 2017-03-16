import urllib
import untangle
import datetime

fellows = ["M Barkeshli", 
           "G W Bryant", 
           "G K Campbell", 
           "Charles W Clark", 
           "S Das Sarma", 
           "V Galitski", 
           "A Gorshkov",
           "M Hafezi",
           "W T Hill",
           "Bei Lok Hu",
           "P S Julienne",
           "B E Kane",
           "P D Lett",
           "C J Lobb",
           "V Manucharyan",
           "A Migdall",
           "C Monroe",
           "L Orozco",
           "K Osborn",
           "W D Phillips",
           "J V Porto",
           "S L Rolston",
           "M S Safronova",
           "J D Sau",
           "G Solomon",
           "I Spielman",
           "J M Taylor",
           "E Tiesinga",
           "E Waks",
           "F C Wellstood",
           "C J Williams",
           "J R Williams",
           "V M Yakovenko"]

message_string = []

def reform_name(fellow):
    name = fellow.split()
    author = name[-1] + '_' + '_'.join(name[0:-1])
    return author

def print_papers(paper_list):
    if len(paper_list) > 0:
        message_string.append('\n*' + fellow + '*')
        for paper in paper_list:
            message_string.append('\n' + paper)

def get_papers(fellow):
    
    author = reform_name(fellow)
    
    url = 'http://export.arxiv.org/api/query?search_query=au:+'+ author + '&sortBy=lastUpdatedDate&sortOrder=descending'
    data = urllib.urlopen(url).read()   
    obj = untangle.parse(data)
    
    paper_list = []

    for entry in obj.feed.entry:
        date = entry.updated.cdata[0:-10]
        datetime_object = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        today = datetime.date.today()
        diff = abs(today - datetime_object).days
        if diff <= time:
            title = entry.title.cdata.replace("\n ", "")
            link = entry.id.cdata
#            paper = link_text(link=link.encode('utf-8'), text=title.encode('utf-8'))
            paper_list.append(title + ' ' + link)
    print_papers(paper_list)
    
time = 7

for fellow in fellows:
    get_papers(fellow)

print(''.join(message_string))
import os
import time
import csv
import urllib
import untangle
import datetime
from slackclient import SlackClient
from bs4 import BeautifulSoup

### Author lists
# Currently only have JQI Fellows in a nice CSV format
jqi_fellows = []
phys_faculty = []
quics_fellows = []
cnam = []
cmtc = []

### Dictionary for affiliation flag lookups
affiliation_lookup = {'jqi' : "Joint Quantum Institute",
                      'phys' : "Department of Physics, University of Maryland",
                      'quics': "Joint Center for Quantum Information and Computer Science"}

author_lookup = {'jqi' : jqi_fellows,
                 'phys': phys_faculty,
                 'quics' : quics_fellows,
                 'cnam' : cnam,
                 'cmtc' : cmtc}

with open('jqi-fellows.csv','rb') as f:
    reader = csv.reader(f)
    for row in reader:
        jqi_fellows.append(row[0])


def reform_name(fellow):
    name = fellow.split()
    author = name[-1] + '_' + '_'.join(name[0:-1])
    return author


def print_papers(paper_list, fellow, message_string):
    if len(paper_list) > 0:
        message_string.append('\n*' + fellow + '*')
        for paper in paper_list:
            message_string.append('\n' + paper)


def get_papers(fellow, time, message_string):

    author = reform_name(fellow)

    url = 'http://export.arxiv.org/api/query?search_query=au:+' + author + '&sortBy=lastUpdatedDate&sortOrder=descending'
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
            paper_list.append(title + ' ' + link)
    print_papers(paper_list, fellow, message_string)


def experimental_search(affiliation_flag):
    if affiliation_lookup[affiliation_flag]:
        # Build up the URL to request
        query = affiliation_lookup[affiliation_flag]
        url = "http://search.arxiv.org:8081/?query=\"" + query + "\"&byDate=1"

        # Grab the html and prase it into a BeautifulSoup object
        html = urllib.urlopen(url).read()
        soup = BeautifulSoup(html, "lxml")

        # Find every td on the page with a class of "snipp"
        results = soup.find_all('td', {'class': 'snipp'})

        # return message header
        message = "Most recent papers with the affiliation *\"" + query + "\"*:\n"

        for paper in results:
            authors = paper.find_all('span', {'class': 'author'})[0].string
            authors = authors.replace('\n', "")
            authors = authors.replace("  ", " ")
            title = paper.find_all('span', {'class': 'title'})[0].string
            title = title.replace('\n', "")
            title = title.replace("  ", " ")
            link = paper.find_all('a', {'class': 'url'})[0].string
            date = paper.find_all('span', {'class': 'age'})[0].string
            date = date.replace("; Indexed ", "")

            message = message + "*" + authors + "*" + "\n" + title + " " + link + "\n"

        return message

    return "Could not find any papers with affiliation *" + query + "*\n"

# arxivbot ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use *author* followed by " + \
               "jqi/quics/phys/cnam/cmtc and a number of days. Or, use " + \
               "*affiliation* followed by jqi/phys/quics/cnam/cmtc. " + \
               "(Note that affiliation search doesn't work yet.)"

    # Possible commands start with "author" or "affiliation"
    if command.startswith("author"):
        print "Fulfilling author search!"
        try:
            # Grab the flag for which list to search
            author_flag = command.split()[1]

            # Return the list based on the key. Defaults to jqi_fellows if key not found
            author_search_list = author_lookup.get(author_flag, jqi_fellows)

            try:
                days = int(command.split()[2]) # days should probably default to some value, like 30 or something
                if days <= 180:
                    message = []
                    for author in author_search_list:
                        get_papers(author, days, message)
                        response = "Papers updated in arXiv from the last " + str(days) + " days:" + ''.join(message)
                else:
                    response = "Please limit days to fewer than 180."
            except:
                print "Couldn't get the days"
                pass
        except:
            print "Couldn't get the flag"
            pass

    if command.startswith("affiliation"):
        print "Fulfilling affiliation search!"
        affiliation_flag = command.split()[1]

        response = experimental_search(affiliation_flag)

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("arXivbot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")

import os
import time
import csv
import urllib
import untangle
import datetime
from slackclient import SlackClient


fellows = []


with open('jqi-fellows.csv','rb') as f:
    reader = csv.reader(f)
    for row in reader:
        fellows.append(row[0])
     
    
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

    
# arxivbot ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "papers"

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
        
    
def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use *" + EXAMPLE_COMMAND + \
               "* followed by the number of days."
    if command.startswith(EXAMPLE_COMMAND):
        try:
            days = int(command.split()[1])
            if days <= 180:
                message = []
                for fellow in fellows:
                    get_papers(fellow, days, message)
                response = "Papers updated in arXiv from the last " + str(days) + " days:" + ''.join(message)
            else:
                response = "Please limit days to fewer than 180."
        except:
            pass
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
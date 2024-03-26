import requests
import xml.etree.ElementTree as ET 
import datetime
import json
import os
import time
import tweepy
from os import listdir
from azure.cosmos import CosmosClient, PartitionKey
from azure.identity import DefaultAzureCredential
ENDPOINT = os.environ['COSMOS_DB_ENDPOINT']                                                         
DATABASENAME = os.environ['COSMOS_DB_NAME']
global CONTAINERNAME
CONTAINERNAME = os.environ['COSMOS_DB_CONTAINER_NAME']                                                                   
CREDENTIAL = os.environ['COSMOS_DB_CREDENTIAL']

#These variables are for Twitter API credentials
CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']                                                      #You need a Twitter dev account to get these credentials and make a tweet.
CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
ACCESS_TOKEN = os.environ['TWITTER_ACCESS_TOKEN']
ACCESS_TOKEN_SECRET = os.environ['TWITTER_ACCESS_TOKEN_SECRET']

import logging
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="mytimer")
@app.schedule(schedule="0 */5 * * * 0-6", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 

def timer_trigger_tweeter(myTimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    if myTimer.past_due:
        logging.info('The timer is past due!')

    global DBENTRYNEWSTIMESTAMPQUERYVALUE
    global DBENTRYNEWSTIMESTAMP
    global DBID
    global XMLQUERYCURRENTDATE
    DBENTRYNEWSTIMESTAMPQUERYVALUE = '{:%a, %d %b %Y}'.format(datetime.datetime.utcnow())
    XMLQUERYCURRENTDATE = [f'{DBENTRYNEWSTIMESTAMPQUERYVALUE}']
    DBENTRYNEWSTIMESTAMP = '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.utcnow())
    DBID = '{:%a, %d %b %Y}'.format(datetime.datetime.utcnow())
    DBQUERYID = '{:%Y-%m-%d}'.format(datetime.datetime.utcnow())
    global client
    global database
    global partitionKeyPath
    global container

    client = CosmosClient(url=ENDPOINT, credential=CREDENTIAL)
    database = client.create_database_if_not_exists(id=DATABASENAME)
    partitionKeyPath = PartitionKey(path="/categoryId")
    container = database.create_container_if_not_exists(id=CONTAINERNAME, partition_key=partitionKeyPath)


    global datesList
    global linksList
    global titleList
    global allPubDates
    datesList = []
    linksList = []
    titleList = []
    allPubDates = []
    global r
    r = None
    r = requests.get("https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/us/rss.xml")
    countEntriesInCosmosDB()
    countEntriesInXML()
    getXMLEntriesMissingFromDB()
    searchForMissingXMLDatesInTheDB()



    list(map(CompareTitlesInDBWithXMLEntriesToPreventDuplicateEntries, linelist))
    RemoveDuplicateXMLEntries()
    list(map(insertIntoCosmosDB,uniqueDates,uniqueTitles,uniqueLinks))
    list(map(MakeTweetWithInsertedEntryInCosmosDB,uniqueDates,uniqueTitles,uniqueLinks))
    datesList = None
    linksList = None

    try:
        deleteAllTxtFiles()
    except Exception as error:
        print("An exception occured: ", error)
    titleList = None
    datesList = None
    linksList = None
    titleList = None
    allPubDates = None


def countEntriesInCosmosDB():
    cosmosDBQuery = None
    EntryNewsTimestamp = None
    params = None
    results = None
    items = None
    listOfItemsInDB = None

    cosmosDBQuery = "SELECT * FROM " +CONTAINERNAME+ " p WHERE p.EntryNewsTimestamp LIKE @EntryNewsTimestamp"                                                                                         
    EntryNewsTimestamp = f"{DBENTRYNEWSTIMESTAMPQUERYVALUE}%"                                               
    params = [dict(name="@EntryNewsTimestamp", value=EntryNewsTimestamp)]                                   
    results = container.query_items(
        query=cosmosDBQuery, parameters=params, enable_cross_partition_query=True
    )

    items = [item for item in results]

    if items == []:
        listOfItemsInDB = []
    if (len(items)) == 0:
        print("No items are found in the database that are todays date.")
    else:
        listOfItemsInDB = []
        x = range(len(items))
        for i in x:
            listOfItemsInDB.append(items[i]["EntryNewsTimestamp"])

    if listOfItemsInDB == []:
        with open("/tmp/MyFunction.Function1Output.txt","a", encoding='utf-8') as file_write:
            print("There are no items in the Cosmos DB. Getting the latest entry in the nytimes rss xml.", file=file_write)
    else:
        print("found items in the DB that are todays date.")
        with open("/tmp/MyFunction.Function1Output.txt","a", encoding='utf-8') as file_write:
            new = '\n'
            print(f"{new.join(listOfItemsInDB)}", file=file_write)



def countEntriesInXML(): 
    f = None
    lines = None
    linelist = None
    root = None
    pubDatez = None
    y = None
    filtered_dates = None
    notInDB = None


    f = open("/tmp/MyFunction.Function1Output.txt", "r", encoding='utf-8')
    lines = f.readlines()
    linelist = []
    for line in lines:
        line = line.replace("\n", "")
        linelist.append(line)
    f.close()

    root = ET.fromstring(r.text)

    pubDatez = [pubDate.text for pubDate in root[0].iter('pubDate')]                               
    pubDatez.pop(0)                                                                                
    y = XMLQUERYCURRENTDATE       #Tue, 16 Jan 2024 - is the timestamp format being followed
    filtered_dates = [date for date in pubDatez if y[0] in date]
    notInDB = []

    if filtered_dates == linelist[0]:                                                                                                           
        print("tThere are no items that need to be added to the db")
        quit
    else:
        for i in filtered_dates:
            if i not in linelist:
                notInDB.append(i)
        else:
            print("THESE ARE THE ITEMS THAT I NEED TO FIND THE DETAILS OF BELOW(ITEMS NOT IN THE DATABASE):")
            print(notInDB)
            new = '\n'
            with open("/tmp/MyFunction.CountEntriesInXML.txt", "a", encoding='utf-8') as file_write:
                for i in notInDB:
                    print(i, file=file_write)



def getXMLEntriesMissingFromDB():
    f = None
    lines = None
    linelist = None
    root = None
    var = None
    loopedPubDates = None




    f = open("/tmp/MyFunction.CountEntriesInXML.txt", "r", encoding='utf-8')
    lines = f.readlines()
    linelist = []
    for line in lines:
        line = line.replace("\n", "")
        linelist.append(line)
    f.close()
    
    root = ET.fromstring(r.text)
    for pubdate in root.iter('channel'):                   
        print("Placeholder text")                                   #Just need this to complete for statement
        for pubdate2 in pubdate.iter('pubDate'):                    
            allPubDates.append(pubdate2.text)
 
    var = [(i) for i in allPubDates]
    for i in range(len(var)):
        if var[i] in linelist:
            print("THE FOLLOWING VALUES ARE THE VALUES MISSING FROM THE DATABASE")
            print(var[(i)])
  
    loopedPubDates = [allPubDates for allPubDates in linelist] 
          
    with open("/tmp/MyFunction.ItemsToFindFromFunc3.txt", "a", encoding='utf-8') as file_write:
        for i in loopedPubDates:
            print(i, file=file_write)


def searchForMissingXMLDatesInTheDB():
    f = None
    f = open("/tmp/MyFunction.ItemsToFindFromFunc3.txt", "r", encoding='utf-8')
    lines = None
    root = None
    pubtitle = None
    pubDatez = None
    pubtitle = None
    publink = None
    pubDatezList = None
    x = None
    pubDatezMatching = None
    indexOfItemsINeedToGet = None


    lines = f.readlines()
    global linelist
    linelist = []
    for line in lines:
        line = line.replace("\n", "")
        linelist.append(line)
    f.close()


    root = ET.fromstring(r.text)
    pubtitle = [title.text for title in root[0].iter('title')]
    todaytitle = pubtitle[2]
    pubDatez = [pubDate.text for pubDate in root[0].iter('pubDate')]
    pubtitle = [title.text for title in root[0].iter('title')]
    publink = [link.text for link in root[0].iter('link')]
    publink.pop(0)
    publink.pop(0)
    pubtitle.pop(0)
    pubtitle.pop(0)
    pubDatez.pop(0)
    pubTitleList = []
    pubLinkList = []
    pubDatezList = pubDatez

    x = range(len(pubDatez))
    for n in x:
        pubTitleList.append(pubtitle[n])
        pubLinkList.append(publink[n])

    pubDatezMatching = ([item for item in pubDatezList if item in linelist])

    print(pubDatezMatching)
    indexOfItemsINeedToGet = [pubDatezList.index(i) for i in pubDatezMatching]

    datesToBeInsertedIntoDB = []
    titlesToBeInsertedIntoDB = []
    linksToBeInsertedIntoDB = []
    test = []

    for i in indexOfItemsINeedToGet:
        print(i, pubDatez[i])
        print(i, pubTitleList[i])
        print(i, pubLinkList[i])
        datesToBeInsertedIntoDB.append(pubDatez[i])
        linksToBeInsertedIntoDB.append(pubLinkList[i])
        titlesToBeInsertedIntoDB.append(pubTitleList[i])
    for i in titlesToBeInsertedIntoDB:
        test.append(i)

    new = '\n'

    with open("/tmp/MyFunction.LinksToFindFromFunc4.txt", "a", encoding='utf-8' ) as file_write:
        for i in linksToBeInsertedIntoDB:
            print(i, file=file_write)
        
    with open("/tmp/MyFunction.DatesToFindFromFunc4.txt", "a", encoding='utf-8') as file_write:
        for i in datesToBeInsertedIntoDB:
            print(i, file=file_write)

    with open("/tmp/MyFunction.TitlesToFindFromFunc4.txt", "a", encoding='utf-8') as file_write:
        for i in titlesToBeInsertedIntoDB:
            print(i, file=file_write)


    f = open("/tmp/MyFunction.TitlesToFindFromFunc4.txt", "r", encoding='utf-8')
    global titles
    titles = f.readlines()
    linelist = []
    for line in titles:
        line = line.replace("\n", "")
        linelist.append(line)
    f.close()

    f = open("/tmp/MyFunction.LinksToFindFromFunc4.txt", "r", encoding='utf-8')
    global links
    links = f.readlines()
    f.close()

    f = open("/tmp/MyFunction.DatesToFindFromFunc4.txt", "r", encoding='utf-8')
    global dates
    dates = f.readlines()
    f.close()




def CompareTitlesInDBWithXMLEntriesToPreventDuplicateEntries(XMLtitlesToCompareWith):
    finalTitlesToBeInserted = []
    finalDatesToBeInserted = []
    finalLinksToBeInserted = []
    EntryNewsTitle = None
    cosmosDBQuery= None
    params = None
    results = None
    items = None
    output = None
    itemsdict = None
    EntryInDB = None
    f = None
    lines = None

    
    print("CompareTitlesInDBWithXMLEntriesToPreventDuplicateEntries")
    cosmosDBQuery = "SELECT * FROM " +CONTAINERNAME+ " p WHERE p.EntryNewsTitle LIKE @EntryNewsTitle"                                                                                        
    EntryNewsTitle = XMLtitlesToCompareWith                                                         
    params = [dict(name="@EntryNewsTitle", value=EntryNewsTitle)]                                           
    results = container.query_items(                                                               
        query=cosmosDBQuery, parameters=params, enable_cross_partition_query=True               
    )


    items = [item for item in results]
    output = json.dumps(items, indent=True)

    if not items:
        print("The item to be inserted is not a duplicate")             #Crude explanation: WHEN YOU GET LATEST ENTRY, MATCH IT WITH LAST ENTRY MADE TO MAKE SURE IT'S NOT A DUPLICATE ENTRY BEING MADE RIGHT NOW, IF IT'S DUPLICATE. SAY ITS DUPLICATE AND THERE ARE NO RELEASES OUT YET TODAY.
    else:
        itemsdict = items[0]                                                                  
        EntryInDB = itemsdict["EntryNewsTitle"]                                                   
    if (len(items)) == 0:
        finalTitlesToBeInserted.append(titles[linelist.index(EntryNewsTitle)])
        finalLinksToBeInserted.append(links[linelist.index(EntryNewsTitle)])
        finalDatesToBeInserted.append(dates[linelist.index(EntryNewsTitle)])

    else:
        listOfTitlesInDB = []
        x = range(len(items))
        for i in x:
            print(items[i]["EntryNewsTitle"] , "is a duplicate. It will not be inserted into the DB or tweeted.")
            listOfTitlesInDB.append(items[i]["EntryNewsTitle"])


    with open("/tmp/MyFunction.DatesToInsert.txt", "a", encoding='utf-8') as file_write:
        for i in finalDatesToBeInserted:
            file_write.writelines(i)

    with open("/tmp/MyFunction.LinksToInsert.txt", "a", encoding='utf-8') as file_write:
        for i in finalLinksToBeInserted:
            file_write.writelines(i)

    with open("/tmp/MyFunction.TitlesToInsert.txt", "a", encoding='utf-8') as file_write:
        for i in finalTitlesToBeInserted:
            file_write.writelines(i)

    f = open("/tmp/MyFunction.TitlesToInsert.txt", "r", encoding='utf-8')
    lines = f.readlines()
    if lines == []:
        print("There is no title to insert since it's most likely a duplicate.")
    else: 
        for line in lines:
            line = line.replace("\n", "")
            titleList.append(line)
    f.close()

    f = open("/tmp/MyFunction.DatesToInsert.txt", "r", encoding='utf-8')
    lines = f.readlines()
    if lines == []:
        print("There is no date to insert since it's most likely a duplicate.")
    else:
        for line in lines:
            line = line.replace("\n", "")
            datesList.append(line)
    f.close()


    f = open("/tmp/MyFunction.LinksToInsert.txt", "r", encoding='utf-8')
    lines = f.readlines()
    if lines == []:
        print("There is no link to insert since it's most likely a duplicate.")
    else:
        for line in lines:
            line = line.replace("\n", "")
            linksList.append(line)
    f.close()



def RemoveDuplicateXMLEntries():
    global uniqueTitles
    global uniqueDates
    global uniqueLinks
    seenTitles = set()
    seenDates = set()
    seenLinks = set()
    uniqueTitles = []
    uniqueDates = []
    uniqueLinks = []
    print("\n Initiating duplicate check number 2 \n")

    for date in datesList:
        if date not in seenDates:
            seenDates.add(date)
            uniqueDates.append(date)
            print(date , "is OK to be inserted into the db. confirmed non-duplicate")
    for title in titleList:
        if title not in seenTitles:
            seenTitles.add(title)
            uniqueTitles.append(title)
            print(title , "is OK to be inserted into the db. confirmed non-duplicate")
    for links in linksList:
        if links not in seenLinks:
            seenLinks.add(links)
            uniqueLinks.append(links)
            print(links , "is OK to be inserted into the db. confirmed non-duplicate")
    

def insertIntoCosmosDB(uniqueDates,uniqueTitles,uniqueLinks):                            
    print("insertIntoCosmosDB")
    DBENTRYNEWSTIMESTAMP = '{:%Y-%m-%d %H:%M:%S.%f}'.format(datetime.datetime.utcnow())

    new_item = {
        "id": DBENTRYNEWSTIMESTAMP,
        "EntryNewsTimestamp": uniqueDates,
        "categoryId": "61dba35b-4f02-45c5-b648-c6badc0cbd79",
        "EntryNewsTitle": uniqueTitles,
        "EntryNewsLink": uniqueLinks
    }

    container.create_item(new_item)
    print("Inserted new item into CosmosDB")



def MakeTweetWithInsertedEntryInCosmosDB(datesToBeInsertedIntoDB,titlesToBeInsertedIntoDB,linksToBeInsertedIntoDB):
    print("MAKING TWEET")
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    client = tweepy.Client(consumer_key = CONSUMER_KEY, consumer_secret = CONSUMER_SECRET, access_token = ACCESS_TOKEN, access_token_secret = ACCESS_TOKEN_SECRET)
    
    global cleanedTweetDate                                            #Removes timezone offset from the tweet text
    cleanedTweetDate = []
    cleanedDate = datesToBeInsertedIntoDB.replace(" +0000", "")
    cleanedTweetDate.append(cleanedDate)
  
    #Try except is here incase the rate limit(50 posts per day. 1,500 per month) for the Twitter API is reached or a duplicate tweet is trying to be tweeted.
    try:
        response = client.create_tweet(text = f"{cleanedDate},\n{titlesToBeInsertedIntoDB}\n{linksToBeInsertedIntoDB}\n")
        print(response)
    except Exception as error:
        print("An exception occured:", error)

    #for future implementation
    #response = client.create_tweet(text = "Bot went down for awhile, This is the latest article:\n" f"{datesToBeInsertedIntoDB},\n{titlesToBeInsertedIntoDB}\n{linksToBeInsertedIntoDB}\n")   



def deleteAllTxtFiles():
    with os.scandir(path="/tmp/") as it:
        for entry in it:
            if entry.name.startswith('MyFunction.') and entry.is_file():
                print(entry.name)
                os.remove(entry)
    print("The program has succesfully executed. Files from /tmp in the Linux OS have been deleted")

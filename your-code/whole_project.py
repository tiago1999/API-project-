import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import random
import time
import os
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import webbrowser
import numpy as np



## connecting to API

def youtube_api(user_input):
    api_key='AIzaSyBrJG3R5SMOyl1Mg-7gKHFpqfUITMDAYmw'

    SortList=['relevance', 'date', 'viewCount', 'rating']

    youtube=build('youtube', 'v3', developerKey=api_key)

    answer_youtube = False
    while answer_youtube == False:

        video_sort_input=input('please select: [0] for Relevance; [1] for Upload date; [2] for View count; [3] for Rating')

        if (video_sort_input == '0') | (video_sort_input == '1') | (video_sort_input == '2') | (video_sort_input == '3'): 
            answer_youtube = True
            r=SortList[int(video_sort_input)]

    ## Request to Youtube top 6 videos on the topic chosen (selected according to the filter inputed by user)
    request = youtube.search().list(
        part='snippet',
        order=r,
        maxResults=6,
        q = user_input
    )
    response = request.execute()


# Creating list and dict of title, description and url of videos on subject selected by user: 

    title_list = []
    description = []
    videoID=[]

    for title in response['items']:
        title_list.append( title['snippet']['title'])
        description.append( title['snippet']['description'])
        videoID.append( title['id']['videoId'])


    title_description = {}

    dictionary = {key: val for key, val in zip(title_list, description)}

    

## Code below creates and stores the URL for the selected videos:

    videoURL=[]
    string1='https://www.youtube.com/watch?v='

    for elements in videoID:
     videoURL.append(string1+elements)



## Compiling a DF with everything [title_list, videoURL, description]
    global videodf
    videodf=pd.DataFrame(list(zip(title_list, videoURL, description)), columns=['Title', 'Link', 'Description'])
    print(videodf.head(6))

    ### to have option of opening one of the URLs:
    x=int(input('Please select number of the video you want to watch'))
    webbrowser.open(videodf.loc[x, 'Link'])
    #open(x)

    


## open youtube pop up 

    # open(x):
    #     webbrowser.open(videodf.loc[x, 'Link'])



## GOOGLE API SECTION

## Find books, connect to the API
google_key='AIzaSyBGu8FOQ_34lF0Uw-m5EDGuTeIlFcLQH3U'
def get_books_api(user_input):

    #url & params
    url = "https://www.googleapis.com/books/v1/volumes"    
    params = {
        'q': user_input,
        'maxResults': 40,
        'key': google_key
    }
    # response
    response = requests.get(url=url, params=params)
    books = response.json()

#sorted_books = books_df.sort_values(['volumeInfo.averageRating'], ascending = False)
    # json to dataframe, sorted by ratings count
    global books_df
    books_df = pd.json_normalize(books['items'])
     
    unique_id = books_df['volumeInfo.industryIdentifiers']
    isbn = pd.json_normalize(pd.json_normalize(unique_id)[1])

    books_df['ISBN'] = isbn['identifier']

    # making presentable catalogue for user 
    global books_catalogue
    books_catalogue= books_df[['volumeInfo.title','volumeInfo.authors','volumeInfo.description','volumeInfo.pageCount','volumeInfo.averageRating', 'volumeInfo.ratingsCount', 'ISBN']]
    books_catalogue.columns= ['Title', 'Author/s', 'Description', 'Pages', 'Rating', '# Reviews', 'ISBN']
    filtered_df = books_catalogue[books_catalogue['ISBN'].apply(lambda x: isinstance(x, str))]
    print(filtered_df)

## getting author bio 

def author_bio_api (author_name):
    author = author_name.replace(' ','_')
    url = 'https://en.wikipedia.org/wiki/'+author

    response = requests.get(url).content

    soup=BeautifulSoup(response, features='lxml')

    element = soup.find_all('p')
    intro1=element[1].text.replace('\n','')

    if len(intro1) < 10:
        print("Sorry, couldn't find the author")
        get_author_bio()
    else:
        return print(intro1)

# downloading books through Selenium

def download_book(user_download):

   user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36"
   options = webdriver.ChromeOptions()
   options.headless = True
   options.add_argument(f'user-agent={user_agent}')
   options.add_argument("--window-size=1920,1080")
   options.add_argument('--ignore-certificate-errors')
   options.add_argument('--allow-running-insecure-content')
   options.add_argument("--disable-extensions")
   options.add_argument("--proxy-server='direct://'")
   options.add_argument("--proxy-bypass-list=*")
   options.add_argument("--start-maximized")
   options.add_argument('--disable-gpu')
   options.add_argument('--disable-dev-shm-usage')
   options.add_argument('--no-sandbox')

   
   driver_1 = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options = options)


   driver_1.get("https://pt1lib.org/")

   time.sleep(1)

   button_select = driver_1.find_element(By.XPATH,"/html/body/table/tbody/tr[2]/td/div/div/div/div[1]/form/div[1]/div/div[1]/input")
   button_select.click()
   time.sleep(2)

   button_select.send_keys(user_download)
   time.sleep(2)

   button_select.send_keys(Keys.ENTER)
   time.sleep(3)

   try:
         
      button_select_book = driver_1.find_element(By.CSS_SELECTOR,"a[href^='/book/']")
      button_select_book.click()
      
   except:
      no_book = input("Couldn't find a book, try another one")
      new_isbn = books_catalogue.loc[books_catalogue['Title'] == no_book, 'ISBN'].values
      download_book(new_isbn)

   time.sleep(3)

   button_select_download=driver_1.find_element(By.CSS_SELECTOR, "div[class^='btn-group']")
   button_select_download.click()

   time.sleep(3)

   return print('Check your downloads ;)')



# get author bio input

def get_author_bio():
    loop = False
    while loop == False:   
        user_author_bio = input("Would you like to read a short bio of any author? If so, write the name of the book of who's author you want to check out. If not, type write 'no'")

        if user_author_bio == 'no':
            loop = True
            download_input = input('Do you want to download any book?')
            download_isbn = books_catalogue.loc[books_catalogue['Title'] == download_input, 'ISBN'].values
            download_book(download_isbn)

        ## fix it 

        elif user_author_bio in list(books_catalogue['Title']):
            try:
                authname = books_catalogue[books_catalogue['Title'] == user_author_bio]['Author/s']
                author_bio_api(authname.values[0][0])
                loop = True
            except:
                print("She/he is not real")

        else: 
            print('You wrote the title wrong, try again.')


# getting downloads input
def download_book_input ():

    download_input = input('Do you want to download any book?')

    download_isbn = books_catalogue.loc[books_catalogue['Title'] == download_input, 'ISBN'].values

    download_book(download_isbn)



initial_input = input('What do you want to learn about')

answer = False
while answer == False:
    

    books_or_videos = input('Would you like to watch videos about ' + initial_input + ' or read books? Type 1 for videos, 2 for books')

    if books_or_videos == '1':
        answer = True
        youtube_api(initial_input)



    elif books_or_videos == '2':
        answer = True
        get_books_api(initial_input)
        get_author_bio()
        download_book_input()

    else:
        print('Wrong input!')
        
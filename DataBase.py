from System import System
from Stock import Stock

import sqlite3
import lxml
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from bs4 import BeautifulSoup
from selenium import webdriver


class DataBase:
    """
    Database class that crawls Google for relevant news articles, extracts important information & adds to SQL Database.
    """

    def __init__(self):
        """
        Class constructor.
        Establishes connection with SQL Database & initializes webdriver for web crawling.
        """
        self.conn = sqlite3.connect("StockDatabase.db")
        self.cur = self.conn.cursor()

        self.articlePageNum = 8
        self.articleSources = ['theguardian']

        self.driver = webdriver.Chrome('chromedriver.exe')

    def addArticles(self, companyName: str) -> None:
        """
        Crawls Google for news articles relevant to companyName, stores article document frequency information
        to SQL Database.

        :param companyName: Name of company to input into Google
        :return: None
        """
        article_texts = self.__searchArticles(companyName)  # {link: text}

        article_lems = {}
        for link in article_texts:
            article_lems[link] = self.__lemmatize(article_texts[link])
            df_string = self.__frequency(article_lems[link])
            self.__updateDataTable(link, df_string, companyName)

    def __searchArticles(self, companyName: str) -> dict:  # {link: text}
        """
        Sub method for self.addArticles method.
        Searches Google Homepage for news articles relevant to CompanyName, returns extracted article texts.

        :param companyName: Name of company to input into Google
        :return: Dictionary with article links as keys and article text as values
        """
        full_articles = {}

        for source in self.articleSources:
            articles = []

            for i in range(self.articlePageNum):
                googleURL = f"https://www.google.com/search?q={companyName}+company+{source}&source=lnms&tbm=nws&start={10 * i}"
                articles += self.__getArticleURL(source, companyName, googleURL)

            for articleURL in articles:
                if self.__existingArticle(articleURL):
                    self.cur.execute(f"select Stocks from Articles where Article_ID = \'{articleURL}\';")
                    cur_stocks = self.cur.fetchone()[0]
                    self.cur.execute(f"update Articles set Stocks = ? where Article_ID = \'{articleURL}\';",
                                     (cur_stocks + f", {companyName}",))
                    self.conn.commit()
                else:
                    extracted = self.__extractArticleText(articleURL)
                    if extracted is not None:
                        full_articles[articleURL] = extracted
        return full_articles

    def __existingArticle(self, article_link: str) -> bool:
        """
        Sub method for self.__searchArticles method.
        Checks if article link already exists in SQL Database.

        :param article_link: Article link to check for overlap
        :return: Whether article_link exists or not
        """
        self.cur.execute(f"select count(*) from Articles where Article_ID = \'{article_link}\';")
        count = self.cur.fetchone()
        return bool(int(count[0]))

    def __getArticleURL(self, source: str, companyName: str, googleURL: str) -> list:  # per Google Page
        """
        Sub method for self.__searchArticles method.
        Crawls given Google search results page to extract all news article links.

        :param source: News source to use (Currently TheGuardian is the only option)
        :param companyName: Name of company inputted into Google
        :param googleURL: URL of current Google search results page
        :return: List of all article URLs
        """
        articles = list()

        self.driver.get(googleURL)
        self.driver.implicitly_wait(10)

        html = self.driver.page_source
        soup = BeautifulSoup(html, "lxml")

        searchData = soup.find("div", attrs={"id": "search"})
        if searchData is None:
            print(googleURL)
            print(searchData)
        data = searchData.findAll('a')
        for d in data:
            article_link = d.attrs['href']
            # print("Check: {}".format(article_link))
            if article_link[12: 12 + len(source)] == source and companyName.lower() in article_link:
                articles.append(article_link)
                # print("Passed: {}".format(article_link))
        # print()
        return articles

    def __extractArticleText(self, articleURL: str) -> str | None:  # per Source Article
        """
        Sub method for self.__searchArticles method.
        Crawls through given news article & extracts all text.

        :param articleURL: Given article link
        :return: Extracted text
        """
        article_text = ""

        self.driver.get(articleURL)
        self.driver.implicitly_wait(10)

        html = self.driver.page_source
        soup = BeautifulSoup(html, "lxml")

        try:
            mainContent = soup.find("div", attrs={"id": "maincontent"})
            data = mainContent.findAll('p')
            for el in data:
                article_text += el.text + " "
            '''
            for text_class in self.sourceTextClass[source]:
                data = soup.findAll('p', attrs={'class': text_class})
                for el in data:
                    full_articles[article] += el.text + " "'''
            return article_text
        except AttributeError:
            return None

    def __lemmatize(self, text: str) -> list:
        """
        Sub method for self.addArticles method.
        Parses given article text, removing stopwords & lemmatizing words into base form.

        :param text: Extracted full article text
        :return: List of lemmatized words
        """
        stop_file = open("stopwords.txt", "r", encoding='utf8')
        stopword_list = stop_file.read().split(" ")
        stop_file.close()
        article_split = word_tokenize(text)
        # print("Length: {}".format(len(article_split)))
        # print(article_split)
        i = 0
        while i < len(article_split):
            if article_split[i].lower() in stopword_list:  # ``, '' included
                article_split.pop(i)
            elif not article_split[i].isalpha():
                article_split.pop(i)
            else:
                i += 1
        # print("Length: {}".format(len(article_split)))
        # print("Article: {}".format(article_split))

        article_pos = pos_tag(article_split)
        article_pos_edit = []
        removed_pos = []

        for (word, pos) in article_pos:
            if pos[0] in ["N", "V", "A", "R", "S"]:  # N: noun, V: verb, A: adj, R: adv, S: satellite adj
                if pos == "NNS":
                    article_pos_edit.append((word[:-1], 'NN'))
                else:
                    article_pos_edit.append((word, pos))
            elif pos[0] == "J":  # JJ - adj
                article_pos_edit.append((word, "ADJ"))
            elif pos[0] == "I":  # IN - ex. amid
                article_pos_edit.append((word, "R"))
            else:
                removed_pos.append((word, pos))

        # print("Pos: {}".format(article_pos))
        # print("Pos Edit: {}".format(article_pos_edit))
        # print("Removed Words: {}".format(removed_pos))

        lemmatizer = WordNetLemmatizer()
        article_lem = [lemmatizer.lemmatize(word.lower(), pos[0].lower()) for (word, pos) in article_pos_edit]
        # print("Lemmatization: {}".format(article_lem))
        return article_lem

    def __frequency(self, article_lem: list) -> str:
        """
        Sub method for self.addArticles method.
        Finds document frequency for each word in lemmatized word list & formats into string for SQL Database input.

        :param article_lem: Lemmatized article words list
        :return: Word frequencies in appropriate string format for SQL
        """
        word_freq = dict()
        for word in article_lem:
            if word in word_freq:
                word_freq[word] += 1
            else:
                word_freq[word] = 1

        tf_string = ""
        for word in word_freq:
            if tf_string == "":
                tf_string = f"({word}, {word_freq[word]})"
            else:
                tf_string += f", ({word}, {word_freq[word]})"
        # print(tf_string)
        return tf_string

    def __updateDataTable(self, link: str, df_string: str, companyName: str) -> None:
        """
        Sub method for self.addArticles method.
        Inserts article document frequency into SQL Database.

        :param link: Article link
        :param df_string: Article document frequency in appropriate string format
        :param companyName: Name of company
        :return: None
        """
        # print(df_string)
        self.cur.execute("insert into Articles values(?, ?, ?)", (link, df_string, companyName))
        self.conn.commit()

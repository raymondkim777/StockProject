from Stock import Stock
from StockData import StockData
from StockGUI import StockGUI

import sqlite3
import spacy
from math import log


class System:
    """
    Overarching System class for organization & main analysis functions.
    """

    def __init__(self):
        """
        Class constructor.
        Establishes connection with SQL Database, loads NLP vector space model, initializes instance variables.
        """
        self.allStockList = []
        self.articleData = None

        self.conn = sqlite3.connect("StockDatabase.db")
        self.cur = self.conn.cursor()

        self.nlp = spacy.load('en_core_web_lg')
        self.keyword_cnt = 10
        self.timePeriod = (('1h', '1mo'), ('1d', '6mo'))

    def addStock(self, stockName: str, companyName: str) -> None:
        """
        Creates Stock object with given arguments. Appends object to self.allStockList for future use.

        :param stockName: Stock symbol for given company
        :param companyName: Company name
        :return: None
        """
        self.allStockList.append(Stock(stockName, companyName))

    def runAllRelAnalysis(self) -> None:
        """
        Uses article data in StockDatabase to calculate TF-IDF to determine keywords for each company.
        Uses vector space model to quantify similarity between companies using the keywords.
        Saves keywords, keyword similarities, and company similarities into StockDatabase.

        :return: None
        """
        # erases current database

        # runs new analysis
        stockLen = len(self.allStockList)
        for i in range(stockLen):
            self.__stockTermCalculate(self.allStockList[i])

        for i in range(0, stockLen - 1):
            for j in range(i + 1, stockLen):
                stock1 = self.allStockList[i]
                stock2 = self.allStockList[j]
                self.__stockRelCalculate(stock1, stock2)
    def __stockTermCalculate(self, stock: Stock) -> bool:
        """
        Sub method for self.runAllRelAnalysis method.

        Calculates TF-IDF for all words in articles relating to certain company (stock).
        Temporarily saves TF-IDF values into Stock object.

        :param stock: Stock object for company in question
        :return: True if successfully calculated TF-IDF, False if already calculated
        """
        if stock.calculated:
            return False
        self.cur.execute(f"select Word_Frequency from Articles where Stocks like \"%{stock.companyName}%\";")
        stock1_tf_list = self.cur.fetchall()
        for word_list in stock1_tf_list:
            if word_list == "":
                continue
            for word_freq in word_list[0][1: -1].split("), ("):
                [word, freq] = word_freq.split(", ")
                if word in stock.tf_idf:
                    stock.tf_idf[word] += int(freq)
                else:
                    stock.tf_idf[word] = int(freq)

        self.cur.execute(f"select count(*) from Articles;")
        doc_num = int(self.cur.fetchone()[0])
        for word in stock.tf_idf:
            self.cur.execute(
                f"select count(*) from Articles where Stocks like \"%{stock.companyName}%\" "
                f"and Word_Frequency like \"%{word}%\";")
            word_idf = int(self.cur.fetchone()[0])
            word_idf = log(doc_num / (1 + word_idf), 10)
            stock.tf_idf[word] *= word_idf

        stock.tf_idf = dict(sorted(stock.tf_idf.items(), key=lambda x: x[1], reverse=True))
        stock.calculated = True
        return True

    def __stockRelCalculate(self, stock1: Stock, stock2: Stock) -> bool:
        """
        Sub method for self.runAllRelAnalysis method.

        Chooses keywords for given stocks.
        Regarding the two given stocks, calculates similarity for all keyword combinations using vector space model.
        Calculates overall similarity for given stocks, assuming basis of 0.25 similarity for significance.
        Company similarity will henceforth be referred to as "relation value".
        Saves all keyword relations and final relation values into StockDatabase.

        :param stock1: Stock object for first company
        :param stock2: Stock object for second company
        :return: True if successfully calculated relation value, False if already calculated
        """
        if stock2 in stock1.RelSentimentScore:
            return False

        self.cur.execute(f"select count(*) from Companies where Name = \'{stock1.companyName}\'")
        if self.cur.fetchone()[0] == 0:
            self.__stockChooseKeywords(stock1)

        self.cur.execute(f"select count(*) from Companies where Name = \'{stock2.companyName}\'")
        if self.cur.fetchone()[0] == 0:
            self.__stockChooseKeywords(stock2)

        stock1.keywordRel[stock2] = [[0 for _ in range(len(stock2.keywords))] for _ in range(len(stock1.keywords))]
        stock2.keywordRel[stock1] = [[0 for _ in range(len(stock1.keywords))] for _ in range(len(stock2.keywords))]

        com1 = stock1.companyName + ", " + stock2.companyName
        com2 = stock2.companyName + ", " + stock1.companyName
        self.cur.execute(f"insert into Relations values (\'{com1}\', null, null)")
        self.cur.execute(f"insert into Relations values (\'{com2}\', null, null)")
        self.conn.commit()

        relations1 = [[0.0 for _ in range(self.keyword_cnt)] for _ in range(self.keyword_cnt)]
        relations2 = [[0.0 for _ in range(self.keyword_cnt)] for _ in range(self.keyword_cnt)]

        relScore = 0
        for i in range(len(stock1.keywords)):
            for j in range(len(stock2.keywords)):
                word1 = stock1.keywords[i]
                word2 = stock2.keywords[j]

                tokens = self.nlp(f"{word1} {word2}")
                curScore = tokens[0].similarity(tokens[1])

                stock1.keywordRel[stock2][i][j] = curScore
                stock2.keywordRel[stock1][j][i] = curScore

                relations1[i][j] = curScore
                relations2[j][i] = curScore

                curScore = (curScore * 10 / 2.5) ** 2
                relScore += curScore

        stock1.RelSentimentScore[stock2] = relScore
        stock2.RelSentimentScore[stock1] = relScore

        insert1 = ""
        insert2 = ""

        for i in range(self.keyword_cnt):
            for j in range(self.keyword_cnt):
                insert1 += str(relations1[i][j]) + ", "
                insert2 += str(relations2[i][j]) + ", "

        self.cur.execute(
            f"update Relations set Relations = \'{insert1[:-2]}\' , "
            f"Final_value = \'{relScore}\' where Companies = \'{com1}\'")
        self.cur.execute(
            f"update Relations set Relations = \'{insert2[:-2]}\' , "
            f"Final_value = \'{relScore}\' where Companies = \'{com2}\'")
        self.conn.commit()

        return True

    def __stockChooseKeywords(self, stock: Stock) -> bool:
        """
        Sub method for self.__stockRelCalculate method.
        Chooses certain number (self.keyword_cnt) of keywords for each stock, based on highest TF-IDF value.
        Saves keywords into StockDatabase.

        :param stock: Stock object for given company
        :return: True for successful keyword selection, False if keywords already exist
        """
        if len(stock.tf_idf) == 0:
            return False

        self.cur.execute(f"insert into Companies values (\'{stock.companyName}\', null)")
        idx = 0
        insert_str = ""
        while len(stock.keywords) < self.keyword_cnt and idx < len(stock.tf_idf):
            keyword = list(stock.tf_idf.keys())[idx]
            if self.nlp(keyword)[0].has_vector:
                stock.keywords.append(keyword)
                insert_str += f"{keyword}, "
            idx += 1
        self.cur.execute(f"update Companies set Keywords = \'{insert_str[:-2]}\' where Name = \'{stock.companyName}\';")
        self.conn.commit()
        return True

    def runAllPredictAnalysis(self) -> bool:
        """
        Runs stock data analysis to determine predicted stock movement.

        :return: None
        """
        # collect past stock data
        for stock in self.allStockList:
            if not StockData.retrieveData(stock, self.timePeriod[0], self.timePeriod[1]):
                return False

        # divide b/w important & nonimportant data change
        for stock in self.allStockList:
            if not StockData.analyzeStockData(stock):
                return False

        return True

    def runStockGUI(self) -> None:
        stockGUI = StockGUI(self.allStockList, self.timePeriod)
        stockGUI.runGUI()

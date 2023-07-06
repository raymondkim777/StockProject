class Stock:
    def __init__(self, stockName, companyName):
        self.stockName = stockName
        self.companyName = companyName

        self.calculated = False
        self.tf_idf = dict()  # {word: tf_idf}
        self.keywords = []  # [word1, word2, ...]
        self.keywordRel = dict()  # {Stock: [[(word2_1) num, (word2_2) num, ...], [], [], ...]}
        self.RelSentimentScore = dict()  # {Stock: float}

        self.stockDataShort = list()  # [price1, price2, ...]
        self.stockDataLong = list()  # [price1, price2, ...]
        self.stockChangeDataShort = list()
        self.stockChangeDataLong = list()
        self.changeImportance = [False, False]

from System import System
from DataBase import DataBase

if __name__ == "__main__":
    system = System()
    # database = DataBase()

    # -- adding stocks to system --
    with open("company_names.txt") as f:
        contents = f.readlines()

    for line in contents:
        line_split = line.split(", ")
        if line_split[1][-1] == '\n':
            line_split[1] = line_split[1][:-1]
        system.addStock(line_split[0], line_split[1])

    # -- adding articles for each stock --
    # for stock in system.allStockList:
        # database.addArticles(stock.companyName)

    # -- running company relation analysis --
    # system.runAllRelAnalysis()

    # -- retrieving stock data & running predictions
    system.runAllPredictAnalysis()
    system.showCompanyRels()

    # -- display analysis results --
    system.runStockGUI()

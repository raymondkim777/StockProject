from Stock import Stock

import yfinance as yf
from statistics import mean, stdev


class StockData:
    """
    StockData static class for collecting live stock data using Yahoo Finance Library.
    """

    @staticmethod
    def retrieveData(stock: Stock, short_term: tuple, long_term: tuple) -> bool:
        """
        Retrieves all stock data for given stock object based on given two time periods.

        :param stock: selected Stock object
        :param short_term: short term time period (interval, period)
        :param long_term: long term time period (interval, period)
        :return: True if all stock data successfully collected, False otherwise
        """
        data = yf.Ticker(stock.stockName)
        stock_df_short = data.history(interval=short_term[0], period=short_term[1], auto_adjust=False)
        stock_df_long = data.history(interval=long_term[0], period=long_term[1], auto_adjust=False)
        stock_df_short = stock_df_short.fillna(method='ffill')
        stock_df_long = stock_df_long.fillna(method='ffill')

        for i in stock_df_short.index:
            stock.stockDataShort.append((stock_df_short.loc[i]['High'] + stock_df_short.loc[i]['Low']) / 2)
        for i in stock_df_long.index:
            stock.stockDataLong.append((stock_df_long.loc[i]['High'] + stock_df_long.loc[i]['Low']) / 2)

        if len(stock.stockDataShort) == 0 or len(stock.stockDataLong) == 0:
            return False

        # short term data
        for i in range(1, len(stock.stockDataShort)):
            stock.stockChangeDataShort.append(stock.stockDataShort[i] - stock.stockDataShort[i - 1])

        # long term data
        for i in range(1, len(stock.stockDataLong)):
            stock.stockChangeDataLong.append(stock.stockDataLong[i] - stock.stockDataLong[i - 1])

        print(
            f"Stock: {stock.companyName}\n"
            f"{stock_df_short.head}\n"
            f"Short Data: {stock.stockDataShort}\n"
            f"{stock_df_long.head}\n"
            f"Long Data: {stock.stockDataLong}"
        )

        return True

    @staticmethod
    def analyzeStockData(stock: Stock) -> bool:
        """
        Analyzes collected stock data for selected stock object to determine significance.

        :param stock: selected Stock object
        :return: True if stock data exists & successful analysis, False otherwise
        """
        if len(stock.stockChangeDataShort) == 0 or len(stock.stockChangeDataLong) == 0:
            return False

        # short term
        change_avg = mean(stock.stockChangeDataShort[:-1])
        change_stdev = stdev(stock.stockChangeDataShort[:-1])
        if change_avg - change_stdev <= stock.stockChangeDataShort[-1] <= change_avg + change_stdev:
            stock.changeImportance[0] = False
        else:
            stock.changeImportance[0] = True

        # long term
        change_avg = mean(stock.stockChangeDataLong[:-1])
        change_stdev = stdev(stock.stockChangeDataLong[:-1])
        if change_avg - change_stdev <= stock.stockChangeDataLong[-1] <= change_avg + change_stdev:
            stock.changeImportance[1] = False
        else:
            stock.changeImportance[1] = True

        return True

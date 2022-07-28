'''
Install yfinance if not installed to run
'''
#pip install yfinance


import numpy as np
import pandas as pd
import pandas_datareader as pdr
import yfinance as yf
import matplotlib.pyplot as plt
import datetime


'''
Setting up class
'''
class Strategies():
    #A class that contains code that strategies later on will inherit from params:
    #codes = list of stock short codes


    #Every class has to have an init method and they define the class specific features.
    #In this case ticker list and two empty dataframes
    def __init__(self,codes):
    #this defines class spacific values
        #so ticker/code list
        self.codes = codes
        #creates 2 empty dataframes
        self.strat = pd.DataFrame()
        self.data = pd.DataFrame()



    def import_data(self, start_date, end_date):
    #this method downloads all data for each backtest from yahoo Finance.
    #and removes any nan values

        #start_date, end_date = string of dates for backtesting with format y-m-d
        #code is another name for ticker
        data = yf.download(self.codes, start_date, end_date)

        #if only one stock code is entered, data is reformatted so that is it the same format as if multiple stock were entered
        if len(self.codes) == 1:
            data.columns = [data.columns, self.codes*len(data.columns)]

        #returns data, and NAN values are removed
        return data.dropna()




    def backtest(self, start_date, end_date):
    #returns a list with elements of a time series from yfinance as well as an array of values between -1 and 1 that represent the strategy over the given period
    #1 represents a long position in one stock, 0 representing a neutral postiion and -1 representing a short position

        #sets up dataframes (defined in the init) to contain data in 1, and then all value weights from the strategy for each stock in the other dataframe
        self.data = self.import_data(start_date, end_date)
        #fills the dataframe with zeros
        self.strat = pd.DataFrame(data = np.zeros([len(self.data), len(self.codes)]), columns = self.codes, index = self.data.index)




    #evaluate method takes a backtest, and evaluates it so calcualte cumulative returns, sharpe and sortino ratios
    def evaluate(self, start_date, end_date, fig_strat=True, fig_other=False, percentage_risk_free_rate = 0.1, **kwargs):
    #returns a dataframe with columns including the daily returns of the portfolio, the cumulative returns, the sharpe ratio and all relevent plot of both the stock price of each stock
    #fig = boolean variable that can be used to produce figures
    #ris_free_rate = average rate of return from a save government issued bond used to calcualte sharpe ratio with
    #**kwargs = any specific keyword arguments that can be passed to the backtesting function to allow for comparison of the backtest for different possible parameters defined in the subclass

        #run the backtest function and define the stock price data to be once again self.data and signals self.strat
        self.strat = self.backtest(start_date, end_date, **kwargs)

        #convert the monthly risk free rate to the daily risk free rate for use when calculating sharpe and sortino ratios
        #e.g. (1+1/100)**(1/21)-1 = (1.01**(0.05)) - 1 =  0.00047 (look up EAR formula)
        #the value of 21 is due to there being 20 trading days in a month
        daily_rate = (1 + percentage_risk_free_rate/100)**(1/21) - 1

        #sets up  new DataFrame which will give the returns of the portfolio
        return_df = pd.DataFrame(columns=["daily returns", "cumulative returns"], index = self.data.index)
        #set return on day 0 to 0
        return_df["daily returns"][0] = 0

        #loops through remaining dates and calculates returns across the portfolio
        for i in range(1, len(self.data)):
            #for each stock, this is 100*value weighting from strategy the previous day*(closing price on current day X - closing price on day X-1)/(closing price on day X-1)
            #hence why if your value weighting is 1 (long position), and the stock goes up, your daily return is posiitve
            #if your weighting is -1 (short position), and the stock goes down, then your daily return is positive
            #this is then summed for the multiple stocks in the portfolio and the portfolio daily returns are given
            return_df["daily returns"][i] = sum(100*self.strat[c][i-1]*(self.data["Adj Close"][c][i]-self.data["Adj Close"][c][i-1])/self.data["Adj Close"][c][i-1] for c in self.codes)

        #calculates the cumulative return for each date
        #it does this by taking the daily return percentage, dividing my 100 and adding 1 to get it into a increase/decrease
        #e.g. daily return of 7% goes >>  (7/100)+1 = 1.07 This happens for all the values in the dataframe
        #then the cumprod returns the cumulative product of a dataframe (NOT SUM) e.g. 1.07*0.96*1.02 not 1.07+0.96+1.02
        #this results is then -1 and multiplied by 100... e.g. (1.12-1)*100 = 12%
        return_df["cumulative returns"] = (((return_df["daily returns"]/100)+1).cumprod()-1)*100
        return_df.dropna()


        #For each of the strategies we went through in the notebook they all require a calculations involving a certain
        #number of historic values. e.g previous percentage returns. As a result our strategies can't start straight away
        #as we need to wait until we have enough previous pieces of data for the code to work and produce signals.

        #calculates the length of time for which the strategy is inactive to begin with
        zero_count = 0
        #While True will run forever until a break command is run.
        while True:
            if sum(abs(self.strat[c].iloc[zero_count]) for c in self.codes):
                #by using iloc[zero_count] when zero_count is 0 it looks at first row, in this is zero then zero_count = 1
                #and then it becomes iloc[1] which searches the second row in the strat dataframe
                #and so on....
                break
            zero_count += 1

            #python syntax allows for the simplification of
            #if not sum(abs(self.strat[c].iloc[zero_count]) for c in self.codes) == 0:
            #to
            #if sum(abs(self.strat[c].iloc[zero_count]) for c in self.codes):

            #^^^^ this basically says that if the rows equals zero, then carry on but if it doesnt equal zero then break
            #so if it is zero 5 times, it bypasses the break and adds to the zero_count, but then the first nonzero value
            #breaks the loop and the while becomes false, and the 5 is stored in zero_count



        #calculates the sharpe ratio, not including the first period of inactivity

        #Sharpe ratio is the sum of the differences in daily returns of the strategy and the risk-free rate
        #over a given period is divivded by the standard devisation of all daily returns.
        #( all return percentages summed/100 - (risk free rate * number of days) ) / standard devisation of all daily returns
        #e.g. ((1.02+0.95+1.06+1.03)/100 - 4*0.0005) / 0.03 = 1.29
        sharpe = ((return_df["daily returns"][zero_count:].sum()/100 - len(return_df[zero_count:]) * daily_rate) / return_df["daily returns"][zero_count:].std())
        print('Sharpe: ', sharpe)

        #Sortino ratio is similar, however we divide by the standard deviation of only the negative or downwards
        #returns (inferring that we only care about negative volatility)
        #This doesnt include the zero_count index in denominator, as there are no negative downturns anyway when there are 0 values, so these are filtered out
        sortino = ((return_df["daily returns"][zero_count:].sum()/100 - len(return_df[zero_count:]) * daily_rate) / return_df["daily returns"][(return_df["daily returns"] < 0)].std())
        print('Sortino: ', sortino)



        #plots figures if fig_strat = TRUE
        if fig_strat:
            #plot of strategy returns
            plt.figure()
            plt.title("Strategy Backtest from" + start_date + " to " + end_date)
            plt.plot(return_df["cumulative returns"])
            plt.show()

        #plots figure if fig_other = TRUE
        if fig_other:
            #plot of all inidividual stocks
            for c in self.codes:
                plt.figure()
                plt.title("Buy and Hold from" + start_date + " to " + end_date + " for " + str(c))
                plt.plot(((self.data["Adj Close"][c].pct_change()+1).cumprod()-1)*100)
                plt.show()
        print('Returns: ', return_df)
        return [return_df, sharpe, sortino]


'''
Class specifically for Time Series Momentum Strat
'''
class StrategyRelativeMomentum(Strategies):

    #p = half the number of stock a position is taken in
    #t = lookback period lenth for calculating momentum of each stock
    #q = time length between portfolio adjustments
    def backtest(self, start_date, end_date, p=2, q=15, t=50):

        #import all code from the parent class
        Strategies.backtest(self, start_date, end_date)

        #loop through each time step to calculate the signals
        for i in range(t, len(self.data)):
            if (i-t) % q == 0:

                #this is similar to the time series momentum Pandas Series,
                #for each time step define a variable signals that is a pd Series with
                #index of stock codes, data equal to the percentage returns over the previous
                #t time steps.
                #however here, we also use sort_values to sort into descending order
                signals = pd.Series(data = (100*(self.data["Adj Close"][c][i-1]-self.data["Adj Close"][c][i-t])/self.data["Adj Close"][c][i-t] for c in self.codes), index = self.codes).sort_values()


                #The following code also normalises the values so they sum to 1:

                #select the p codes with a long position (looking at the end of the sorted Series)
                for c in signals[-p:].keys():
                    self.strat[c][i] = 1/(2*p)

                #select p codes with short position by looking at start of Series
                for c in signals[:p].keys():
                    self.strat[c][i] = -1/(2*p)

            else:
                self.strat.iloc[i] = self.strat.iloc[i-1]
        return self.strat




'''
Example of a backtest for this strat
'''
testRM = StrategyRelativeMomentum(["HG=F","GC=F","ZC=F", "SI=F", "PA=F","RB=F"])
testRM.evaluate("2020-07-25","2022-07-25", t=50)

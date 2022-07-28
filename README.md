# RelativeMomentumTradingStrategy

This again, like my Time Momentum and Buy and Hold algorithms uses the Strategies class as a basis.

Here we will implement a backtest for the relative momentum strategy.

This is a similar strategy to the time series momentum, but instead of gonig short and long on all stocks, we only go long the the best 'p' performing stocks, and short the worst p performing stocks.

So the loockback period is still the previous t days and we still only adjust the portfolio every q days.

As usual, across a row in the strat dataframe, the ABSOLUTE values must all add up to 1. Therefore, the weights for the worst stocks are -1/(2p) and for the best p stocks 1/(2p) which if you take the ABSOLUTE values, then they will add to 1.

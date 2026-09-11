Feature: Historical backtesting
  As a freelance investor
  I want to replay a screen against real historical prices
  So that I can see when it would have matched and how those matches performed

  Scenario: A backtest records a match on each day price satisfies the screen
    Given a symbol with 5 days of historical prices around a threshold
    When I backtest a "price below threshold" screen over that window
    Then the timeline contains a match for each day price was below the threshold

  Scenario: Fundamentals are frozen at today's values during a backtest
    Given a symbol with a P/E ratio of 15 today and price history that varies
    When I backtest a screen requiring P/E at or below 20
    Then every day in the window matches, since P/E never changes during the backtest

  Scenario: A symbol with no price history in the window is excluded
    Given a symbol whose price history starts after the backtest window
    When I backtest a screen that would otherwise match
    Then that symbol is listed in excluded symbols

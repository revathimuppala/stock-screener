Feature: Watchlist
  As a freelance investor
  I want to track a personal list of symbols
  So that I can revisit stocks I'm interested in without re-screening

  Scenario: Add a symbol to the watchlist
    Given an empty watchlist
    When I add symbol "AAPL" to the watchlist
    Then the watchlist contains "AAPL"

  Scenario: Remove a symbol from the watchlist
    Given a watchlist containing "AAPL"
    When I remove symbol "AAPL" from the watchlist
    Then the watchlist does not contain "AAPL"

  Scenario: Adding the same symbol twice is idempotent
    Given a watchlist containing "AAPL"
    When I add symbol "AAPL" to the watchlist
    Then the watchlist contains "AAPL" exactly once

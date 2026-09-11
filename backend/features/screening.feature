Feature: Stock screening
  As a freelance investor
  I want to filter the stock universe by fundamental criteria
  So that I can find candidates worth researching further

  Scenario: Screen stocks by P/E range
    Given a universe of stocks with known fundamentals
    When I screen with a P/E range of 10 to 20
    Then every result has a P/E ratio between 10 and 20

  Scenario: Screen stocks by sector and minimum dividend yield
    Given a universe of stocks with known fundamentals
    When I screen for sector "Technology" with minimum dividend yield 0.01
    Then every result is in sector "Technology"
    And every result has a dividend yield of at least 0.01

  Scenario: Empty result set is not an error
    Given a universe of stocks with known fundamentals
    When I screen with a P/E range of 0 to 0.01
    Then the response status is "ok"
    And the results list is empty

  Scenario: Screener falls back to cached data when the provider is down
    Given a universe of stocks with known fundamentals
    And the data provider is currently down
    And the cache holds fresh-enough data for every symbol
    When I screen with no criteria
    Then the response status is "degraded"
    And every result is marked stale

  Scenario: A single bad symbol does not fail the whole screen
    Given a universe of stocks with known fundamentals
    And one symbol has no data available from the provider or the cache
    When I screen with no criteria
    Then the response status is "degraded"
    And that symbol is listed in excluded symbols
    And results are still returned for the remaining symbols

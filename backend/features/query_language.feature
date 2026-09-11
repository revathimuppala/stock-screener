Feature: Query language screening
  As a freelance investor
  I want to write a boolean expression over stock fields
  So that I can express screens the structured filter form can't

  Scenario: A simple comparison matches the right stocks
    Given a universe of stocks with known fundamentals
    When I screen with the query: pe < 20
    Then every result has a P/E ratio below 20

  Scenario: A compound AND/OR query with grouping
    Given a universe of stocks with known fundamentals
    When I screen with the query: (roe > 0.15 OR pe < 10) AND sector = "Technology"
    Then every result is in sector "Technology"

  Scenario: An invalid query is rejected before touching data
    Given a universe of stocks with known fundamentals
    When I screen with the query: not_a_real_field < 20
    Then the query is rejected with a parse error

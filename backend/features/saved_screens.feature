Feature: Saved screens
  As a freelance investor
  I want to save a screen and re-run it later
  So that I don't have to re-enter the same filters every time

  Scenario: Save a criteria-based screen
    Given no saved screens
    When I save a screen named "Cheap tech" with a P/E max of 20
    Then the saved screens list contains "Cheap tech"

  Scenario: Running a saved screen re-executes it against current data
    Given a saved screen named "Cheap tech" with a P/E max of 20
    And a universe of stocks with known fundamentals
    When I run the saved screen "Cheap tech"
    Then every result has a P/E ratio at or below 20

  Scenario: Delete a saved screen
    Given a saved screen named "Cheap tech" with a P/E max of 20
    When I delete the saved screen "Cheap tech"
    Then the saved screens list does not contain "Cheap tech"

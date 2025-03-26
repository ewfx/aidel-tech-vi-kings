Feature: Sanctions Detection
  As a financial compliance officer
  I want to identify transactions involving sanctioned entities
  So that I can block prohibited transactions

  Scenario: Detecting a sanctioned organization
    Given a transaction with the following content:
      """
      Transaction ID: TEST-SANC-002
      Date: 2023-09-21 14:30:00

      Sender:
      Name: European Trade Solutions GmbH
      Account: DE89 3704 0044 0532 0130 00 (Deutsche Bank)
      Address: Friedrichstrasse 123, Berlin, Germany

      Receiver:
      Name: Sberbank of Russia
      Account: RU12 3456 7890 1234 5678 9012
      Address: Moscow, Russia

      Amount: $750,000 USD
      Transaction Type: SWIFT Transfer
      Reference: Equipment Purchase Contract #ER-789

      Additional Notes:
      Transfer related to energy sector equipment
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the risk score should be at least 0.8
    And the extracted entities should include:
      | European Trade Solutions GmbH |
      | Sberbank of Russia           |
    And the reasoning should include any of:
      | sanction         |
      | russia           |
      | restricted       |
    And the evidence should include any of:
      | sanction         |
      | russia           |
    # Assessment data validation
    And the assessment data should include the transaction text
    And the assessment data should include organization "European Trade Solutions GmbH"
    And the assessment data should include organization "Sberbank of Russia"
    And organization "Sberbank of Russia" should have data from "sanctions"
    And organization "Sberbank of Russia" should have data from "wikidata"
    And at least 1 sanctions results should be included in the assessment data
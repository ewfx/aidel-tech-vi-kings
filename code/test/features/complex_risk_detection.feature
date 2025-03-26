Feature: Complex Risk Detection
  As a financial compliance officer
  I want to identify transactions with multiple risk factors
  So that I can apply comprehensive risk mitigation measures

  Scenario: Detecting a complex network of high-risk entities
    Given a transaction with the following content:
      """
      Transaction ID: TEST-COMPLEX-004
      Date: 2023-09-23 16:20:00

      Sender:
      Name: Gazprom Export LLC
      Account: RU98 7654 3210 9876 5432 10
      Address: St. Petersburg, Russia

      Receiver:
      Name: Almaz Trading FZE
      Account: AE123456789012345678
      Address: Dubai, UAE

      Beneficiary Owner: Dmitry Medvedev Foundation
      Reference: Almaz Project Funding

      Amount: $4,750,000 USD
      Transaction Type: SWIFT Transfer

      Additional Notes:
      Transfer approved by Director of Operations
      Final beneficiary: Cyprus Holding Company managed by trustee Igor Shuvalov
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the risk score should be at least 0.9
    And the extracted entities should include:
      | Gazprom Export LLC           |
      | Almaz Trading FZE            |
      | Dmitry Medvedev Foundation   |
      | Igor Shuvalov                |
    And the reasoning should include any of:
      | sanction         |
      | pep              |
      | politically exposed |
      | russia           |
      | state-owned      |
      | medvedev         |
      | president        |
      | shuvalov         |
      | deputy           |
    And the evidence should include any of:
      | sanction            |
      | pep                 |
      | politically exposed |
    # Assessment data validation
    And the assessment data should include the transaction text
    And the assessment data should include organization "Gazprom Export LLC"
    And the assessment data should include organization "Almaz Trading FZE"
    And the assessment data should include organization "Dmitry Medvedev Foundation"
    And the assessment data should include person "Igor Shuvalov"
    And organization "Gazprom Export LLC" should have data from "sanctions"
    And organization "Gazprom Export LLC" should have data from "wikidata"
    And person "Igor Shuvalov" should have data from "pep"
    And at least 2 sanctions results should be included in the assessment data
    And at least 1 PEP results should be included in the assessment data
    And the assessment data should include Wikidata-discovered people
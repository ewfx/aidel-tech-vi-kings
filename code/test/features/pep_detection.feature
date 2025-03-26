Feature: PEP Detection
  As a financial compliance officer
  I want to identify transactions involving politically exposed persons (PEPs)
  So that I can apply enhanced due diligence measures

  Scenario: Detecting a direct PEP in a transaction
    Given a transaction with the following content:
      """
      Transaction ID: TEST-PEP-001
      Date: 2023-09-20 10:15:00

      Sender:
      Name: "Global Horizons Consulting LLC"
      Account: IBAN CH56 0483 5012 3456 78009 (Swiss bank)
      Address: Rue du Marché 17, Geneva, Switzerland

      Receiver:
      Name: "PUTIN"
      Account: 987654321 (Bank of Cyprus)
      Address: Limassol, Cyprus

      Amount: $1,500,000 USD
      Transaction Type: Wire Transfer
      Reference: Investment Consulting Services

      Additional Notes:
      Urgent transfer approved by Managing Director
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the risk score should be at least 0.7
    And the extracted entities should include:
      | Global Horizons Consulting LLC |
      | PUTIN   |
    And the reasoning should include any of:
      | pep                 |
      | politically exposed |
      | sanction            |
    And the evidence should include any of:
      | pep                 |
      | politically exposed |
      | sanction            |
    # Assessment data validation
    And the assessment data should include the transaction text
    And the assessment data should include organization "Global Horizons Consulting LLC"
    And the assessment data should include person "PUTIN"
    And person "PUTIN" should have data from "pep"
    And person "PUTIN" should have data from "sanctions"
    And at least 1 PEP results should be included in the assessment data

  Scenario: Detecting an organization with a PEP connection
    Given a transaction with the following content:
      """
      Transaction ID: TEST-INDIRECT-003
      Date: 2023-09-22 09:45:00

      Sender:
      Name: Western Contractors Inc.
      Account: US12 3456 7890 1234 5678 90
      Address: 123 Main Street, New York, USA

      Receiver:
      Name: Rosemont Seneca Partners LLC
      Account: US98 7654 3210 9876 5432 10
      Address: Washington DC, USA

      Amount: $2,300,000 USD
      Transaction Type: Wire Transfer
      Reference: Strategic Consulting Services

      Additional Notes:
      Partnership agreement signed by Hunter Biden, Managing Partner
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the risk score should be at least 0.6
    And the extracted entities should include:
      | Western Contractors Inc.      |
      | Rosemont Seneca Partners LLC  |
      | Hunter Biden                  |
    And the reasoning should include any of:
      | pep                 |
      | politically exposed |
      | sanction            |
    # Assessment data validation
    And the assessment data should include the transaction text
    And the assessment data should include organization "Western Contractors Inc."
    And the assessment data should include organization "Rosemont Seneca Partners LLC"
    And the assessment data should include person "Hunter Biden"
    And person "Hunter Biden" should have data from "pep"
    And organization "Rosemont Seneca Partners LLC" should have data from "wikidata"
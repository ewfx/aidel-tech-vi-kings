Feature: Data Source Verification
  As a financial compliance officer
  I want to verify results from different data sources
  So that I can ensure the risk assessment system is collecting all relevant information

  Scenario: Verifying OpenCorporates data retrieval
    Given a transaction with the following content:
      """
      Transaction ID: TEST-OPENCORP-001
      Date: 2023-09-25 09:15:00

      Sender:
      Name: Global Commerce Bank
      Account: GB29 NWBK 6016 1331 9268 19
      Address: 123 Finance Street, London, UK

      Receiver:
      Name: ExxonMobil Corporation
      Account: US12 3456 7890 1234 5678 90
      Address: 5959 Las Colinas Boulevard, Irving, Texas, USA

      Amount: $2,500,000 USD
      Transaction Type: Wire Transfer
      Reference: Energy Project Funding 2023-Q3

      Additional Notes:
      Standard quarterly payment for ongoing project
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the OpenCorporates data should include company information for "ExxonMobil Corporation"
    And the OpenCorporates data should show jurisdiction "usa" for "ExxonMobil Corporation"
    # Assessment data validation
    And the assessment data should include the transaction text
    And the assessment data should include organization "Global Commerce Bank"
    And the assessment data should include organization "ExxonMobil Corporation"
    And organization "ExxonMobil Corporation" should have data from "opencorporates"
    And organization "ExxonMobil Corporation" should have data from "wikidata"

  Scenario: Verifying Wikidata entity discovery
    Given a transaction with the following content:
      """
      Transaction ID: TEST-WIKIDATA-001
      Date: 2023-09-27 14:45:00

      Sender:
      Name: Tech Investment Partners LLC
      Account: US87 1234 5678 9012 3456 78
      Address: 1 Venture Way, San Francisco, CA, USA

      Receiver:
      Name: Rosneft Oil Company
      Account: RU12 3456 7890 1234 5678 90
      Address: Moscow, Russia

      Amount: $1,750,000 USD
      Transaction Type: SWIFT Transfer
      Reference: Technology Licensing Agreement #RN-2023-T45

      Additional Notes:
      Approved by Board of Directors
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the Wikidata data should include entity information for "Rosneft Oil Company"
    And the Wikidata data should discover associated people
    And at least one discovered person should have role containing "executive"
    # Assessment data validation
    And the assessment data should include the transaction text
    And the assessment data should include organization "Tech Investment Partners LLC"
    And the assessment data should include organization "Rosneft Oil Company"
    And organization "Rosneft Oil Company" should have data from "wikidata"
    And organization "Rosneft Oil Company" should have data from "sanctions"
    And the assessment data should include Wikidata-discovered people
    And a Wikidata-discovered person should have role containing "executive"

  Scenario: Verifying PEP detection from multiple sources
    Given a transaction with the following content:
      """
      Transaction ID: TEST-PEP-MULTI-001
      Date: 2023-09-28 11:00:00

      Sender:
      Name: Swiss Private Banking SA
      Account: CH56 0483 5012 3456 7890 1
      Address: Bahnhofstrasse 45, Zurich, Switzerland

      Receiver:
      Name: Global Investment Holdings
      Account: CY17 0020 0128 0000 0012 0052 7600
      Address: 25 Aphrodite Avenue, Nicosia, Cyprus

      Amount: $3,250,000 USD
      Transaction Type: Wire Transfer
      Reference: Private Investment Fund Transfer

      Additional Notes:
      Authorized by Mr. Petro Poroshenko, Ultimate Beneficial Owner
      Investment managed by Mrs. Yulia Tymoshenko as advisor
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the PEP data should include matches for "Petro Poroshenko"
    And the PEP data should include matches for "Yulia Tymoshenko"
    And the PEP data should show "Ukraine" as country for at least one person
    And the risk score should be at least 0.80
    # Assessment data validation
    And the assessment data should include the transaction text
    And the assessment data should include organization "Swiss Private Banking SA"
    And the assessment data should include organization "Global Investment Holdings"
    And the assessment data should include person "Petro Poroshenko"
    And the assessment data should include person "Yulia Tymoshenko"
    And person "Petro Poroshenko" should have data from "pep"
    And person "Yulia Tymoshenko" should have data from "pep"
    And at least 2 PEP results should be included in the assessment data
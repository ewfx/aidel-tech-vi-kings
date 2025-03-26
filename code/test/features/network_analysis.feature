Feature: Network Analysis and Risk Profiling
  As a financial investigator
  I want to analyze complex entity networks and transaction patterns
  So that I can identify sophisticated money laundering schemes

  Scenario: Detecting shell company patterns
    Given a transaction with the following content:
      """
      Transaction ID: TEST-SHELL-001
      Date: 2023-10-01 08:30:00

      Sender:
      Name: "Oceanic Holdings Ltd"
      Account: VG24 BVIR 0000 0123 4567 8901
      Address: Tortola, British Virgin Islands

      Receiver:
      Name: "Global Strategic Investments LLC"
      Account: AE07 0331 2345 6789 0123 456
      Address: Dubai Multi Commodities Centre, UAE

      Amount: $3,750,000 USD
      Transaction Type: SWIFT Transfer
      Reference: Project Sunrise Investment

      Additional Notes:
      Authorized by Ms. Elena Petrova (signatory)
      Final beneficiary: Alpha Crown Services Ltd (Seychelles)
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the risk score should be at least 0.85
    And the extracted entities should include:
      | Oceanic Holdings Ltd            |
      | Global Strategic Investments LLC |
      | Alpha Crown Services Ltd        |
      | Elena Petrova                   |
    And the reasoning should include any of:
      | shell company     |
      | offshore          |
      | high-risk jurisdiction |
      | layering          |
      | beneficial owner  |
    And at least 3 distinct risk factors should be identified
    # Assessment data validation
    And the assessment data should include the transaction text
    And the assessment data should include organization "Oceanic Holdings Ltd"
    And the assessment data should include organization "Global Strategic Investments LLC"
    And the assessment data should include organization "Alpha Crown Services Ltd"
    And the assessment data should include person "Elena Petrova"
    And organization "Oceanic Holdings Ltd" should have data from "opencorporates"
    And organization "Oceanic Holdings Ltd" should have data from "sanctions"
    And person "Elena Petrova" should have data from "pep"

  Scenario: Identifying beneficial ownership concerns
    Given a transaction with the following content:
      """
      Transaction ID: TEST-UBO-001
      Date: 2023-10-04 16:00:00

      Sender:
      Name: "Global Investment Trust S.A."
      Account: LU28 0019 4006 4475 0000
      Address: Luxembourg City, Luxembourg

      Receiver:
      Name: "Eastern Development Corporation"
      Account: HK12 3456 7890 1234 5678
      Address: Central, Hong Kong

      Amount: $12,500,000 USD
      Transaction Type: Wire Transfer
      Reference: Strategic Investment Fund Allocation

      Additional Notes:
      Trust beneficiaries include family members of Viktor Yanukovych
      Investment managed by Thomas Holdings Ltd (Cayman Islands)
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the risk score should be at least 0.85
    And the extracted entities should include:
      | Global Investment Trust S.A.     |
      | Eastern Development Corporation  |
      | Viktor Yanukovych                |
      | Thomas Holdings Ltd              |
    And the beneficial ownership analysis should identify PEP connections
    And the risk assessment should identify layered ownership structures
    And the evidence should include any of:
      | beneficial owner  |
      | complex structure |
      | pep connection    |
    # Assessment data validation
    And the assessment data should include the transaction text
    And the assessment data should include organization "Global Investment Trust S.A."
    And the assessment data should include organization "Eastern Development Corporation"
    And the assessment data should include organization "Thomas Holdings Ltd"
    And the assessment data should include person "Viktor Yanukovych"
    And person "Viktor Yanukovych" should have data from "pep"
    And at least 1 PEP results should be included in the assessment data
    And the assessment data should include Wikidata-discovered people
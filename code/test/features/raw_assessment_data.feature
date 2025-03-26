Feature: Raw Assessment Data Validation
  As a financial compliance officer
  I want to verify that raw assessment data is correctly collected and structured
  So that I can ensure risk assessments are based on complete information

  Scenario: Validating comprehensive assessment data collection
    Given a transaction with the following content:
      """
      Transaction ID: TEST-DATA-001
      Date: 2023-10-10 09:30:00

      Sender:
      Name: Falcon International Trading LLC
      Account: AE560123456789012345678
      Address: Dubai International Financial Centre, UAE

      Receiver:
      Name: Baltic Business Partners OÜ
      Account: EE382200221020145685
      Address: Tallinn, Estonia

      Amount: $2,850,000 USD
      Transaction Type: Wire Transfer
      Reference: Investment Services Contract #FBP-2023-104

      Additional Notes:
      Approved by Alexander Ponomarenko (Chairman)
      Ultimate beneficiary: Arctic Resource Ventures Ltd (BVI)
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the assessment data should include the transaction text
    And the assessment data should include organization "Falcon International Trading LLC"
    And the assessment data should include organization "Baltic Business Partners OÜ"
    And the assessment data should include organization "Arctic Resource Ventures Ltd"
    And the assessment data should include person "Alexander Ponomarenko"
    And organization "Falcon International Trading LLC" should have data from "opencorporates"
    And organization "Falcon International Trading LLC" should have data from "sanctions"
    And organization "Falcon International Trading LLC" should have data from "wikidata"
    And organization "Baltic Business Partners OÜ" should have data from "opencorporates"
    And person "Alexander Ponomarenko" should have data from "pep"
    And person "Alexander Ponomarenko" should have data from "sanctions"

  Scenario: Validating cross-referenced entity detection
    Given a transaction with the following content:
      """
      Transaction ID: TEST-XREF-001
      Date: 2023-10-11 14:15:00

      Sender:
      Name: VTB Bank PJSC
      Account: RU40 3012 3456 7890 1234 5678
      Address: St. Petersburg, Russia

      Receiver:
      Name: Swiss Asset Management AG
      Account: CH93 0076 2011 6238 5295 7
      Address: Zurich, Switzerland

      Amount: $5,500,000 USD
      Transaction Type: SWIFT Transfer
      Reference: Asset Management Services

      Additional Notes:
      Transaction approved by Igor Sechin
      For investment portfolio management services
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the assessment data should include the transaction text
    And the assessment data should include organization "VTB Bank PJSC"
    And the assessment data should include organization "Swiss Asset Management AG"
    And the assessment data should include person "Igor Sechin"
    And organization "VTB Bank PJSC" should have data from "sanctions"
    And organization "VTB Bank PJSC" should have data from "wikidata"
    And person "Igor Sechin" should have data from "pep"
    And person "Igor Sechin" should have data from "sanctions"
    And the assessment data should include Wikidata-discovered people
    And at least 1 sanctions results should be included in the assessment data
    And at least 1 PEP results should be included in the assessment data

  Scenario: Validating multi-jurisdiction entity assessment
    Given a transaction with the following content:
      """
      Transaction ID: TEST-MULTI-JUR-001
      Date: 2023-10-12 11:30:00

      Sender:
      Name: Cayman Investment Partners Ltd
      Account: KY56 0123 4567 8901 2345 6789
      Address: George Town, Cayman Islands

      Receiver:
      Name: Hong Kong Strategic Ventures Limited
      Account: HK12 3456 7890 1234 5678
      Address: Central, Hong Kong

      Amount: $7,250,000 USD
      Transaction Type: Wire Transfer
      Reference: Capital Contribution - Project Phoenix

      Additional Notes:
      Investment funding for Singapore infrastructure project
      Co-investors include Jersey Finance Ltd and Macau Trading Company
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the assessment data should include the transaction text
    And the assessment data should include organization "Cayman Investment Partners Ltd"
    And the assessment data should include organization "Hong Kong Strategic Ventures Limited"
    And the assessment data should include organization "Jersey Finance Ltd"
    And the assessment data should include organization "Macau Trading Company"
    And organization "Cayman Investment Partners Ltd" should have data from "opencorporates"
    And organization "Hong Kong Strategic Ventures Limited" should have data from "opencorporates"
    And at least 4 different jurisdictions should be referenced in the assessment data

  Scenario: Validating entity network discovery
    Given a transaction with the following content:
      """
      Transaction ID: TEST-NETWORK-001
      Date: 2023-10-13 15:45:00

      Sender:
      Name: Gazprombank JSC
      Account: RU98 7654 3210 9876 5432 10
      Address: Moscow, Russia

      Receiver:
      Name: Central European Trading GmbH
      Account: AT61 1904 3002 3457 3201
      Address: Vienna, Austria

      Amount: $3,850,000 USD
      Transaction Type: SWIFT Transfer
      Reference: Energy Sector Consultation

      Additional Notes:
      Approved by Alexei Miller, Chairman
      Related to Nord Stream 2 project consultation services
      """
    When I submit the transaction
    And I wait for the transaction to complete
    Then the transaction status should be "completed"
    And the assessment data should include the transaction text
    And the assessment data should include organization "Gazprombank JSC"
    And the assessment data should include organization "Central European Trading GmbH"
    And the assessment data should include person "Alexei Miller"
    And organization "Gazprombank JSC" should have data from "sanctions"
    And organization "Gazprombank JSC" should have data from "wikidata"
    And person "Alexei Miller" should have data from "pep"
    And the assessment data should include Wikidata-discovered people
    And a Wikidata-discovered person should have role containing "executive"
    And at least 3 interconnected entities should be identified in the assessment data
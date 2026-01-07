Feature: Chat Storage Stage Data Persistence
  As a user of the LLM Council application
  I want the deliberation stage data to be fully preserved
  So that I can review the complete council process later

  Background:
    Given a registered user exists in the system
    And the user has an existing chat

  Scenario: Stage one model responses are preserved
    When the assistant saves a message with stage one containing multiple model responses
    Then each model response should be retrievable
    And the model identifiers should be preserved
    And the response content should be preserved

  Scenario: Stage two rankings are preserved
    When the assistant saves a message with stage two containing peer rankings
    Then the ranking evaluations should be retrievable
    And the parsed rankings should be preserved

  Scenario: Stage three synthesis is preserved
    When the assistant saves a message with stage three synthesis
    Then the synthesized response should be retrievable
    And the chairman model output should be preserved

  Scenario: All stages are retrieved together
    Given the chat contains an assistant message with all three stages
    When the user retrieves messages from the chat
    Then each stage should be present in the assistant message
    And no stage data should be lost or corrupted

  Scenario: Stage data with complex nested structures is preserved
    When the assistant saves a message with deeply nested stage data
    Then the nested structure should be fully preserved
    And the data should be retrievable in its original form

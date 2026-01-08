Feature: Stage Collapse Icons
  As a user of the LLM Council interface
  I want to collapse and expand individual stages
  So that I can focus on the content I care about without scrolling through everything

  Background:
    Given the user has a conversation with council responses displayed
    And all stages are visible with their content

  # Happy Path Scenarios

  Scenario: User collapses Stage 1 by clicking the collapse icon
    Given Stage 1 is expanded showing its content
    When the user clicks the collapse icon on Stage 1
    Then Stage 1 content is hidden
    And the Stage 1 title remains visible
    And the collapse icon rotates to indicate collapsed state

  Scenario: User expands a collapsed Stage 1 by clicking the collapse icon
    Given Stage 1 is collapsed showing only its title
    When the user clicks the collapse icon on Stage 1
    Then Stage 1 content is visible
    And the collapse icon rotates to indicate expanded state

  Scenario: User collapses Stage 2 by clicking the collapse icon
    Given Stage 2 is expanded showing its content
    When the user clicks the collapse icon on Stage 2
    Then Stage 2 content is hidden
    And the Stage 2 title remains visible
    And the collapse icon rotates to indicate collapsed state

  Scenario: User expands a collapsed Stage 2 by clicking the collapse icon
    Given Stage 2 is collapsed showing only its title
    When the user clicks the collapse icon on Stage 2
    Then Stage 2 content is visible
    And the collapse icon rotates to indicate expanded state

  Scenario: User collapses Stage 3 by clicking the collapse icon
    Given Stage 3 is expanded showing its content
    When the user clicks the collapse icon on Stage 3
    Then Stage 3 content is hidden
    And the Stage 3 title remains visible
    And the collapse icon rotates to indicate collapsed state

  Scenario: User expands a collapsed Stage 3 by clicking the collapse icon
    Given Stage 3 is collapsed showing only its title
    When the user clicks the collapse icon on Stage 3
    Then Stage 3 content is visible
    And the collapse icon rotates to indicate expanded state

  Scenario: User collapses Stage 4 by clicking the collapse icon
    Given Stage 4 is expanded showing its content
    When the user clicks the collapse icon on Stage 4
    Then Stage 4 content is hidden
    And the Stage 4 title remains visible
    And the collapse icon rotates to indicate collapsed state

  Scenario: User expands a collapsed Stage 4 by clicking the collapse icon
    Given Stage 4 is collapsed showing only its title
    When the user clicks the collapse icon on Stage 4
    Then Stage 4 content is visible
    And the collapse icon rotates to indicate expanded state

  # Independence Scenarios

  Scenario: Collapsing one stage does not affect other stages
    Given all stages are expanded
    When the user clicks the collapse icon on Stage 2
    Then Stage 2 content is hidden
    And Stage 1 content remains visible
    And Stage 3 content remains visible

  Scenario: Multiple stages can be collapsed independently
    Given all stages are expanded
    When the user clicks the collapse icon on Stage 1
    And the user clicks the collapse icon on Stage 3
    Then Stage 1 content is hidden
    And Stage 2 content remains visible
    And Stage 3 content is hidden

  # Default State Scenarios

  Scenario: Stages are expanded by default when conversation loads
    Given the user opens a conversation with council responses
    Then Stage 1 is expanded showing its content
    And Stage 2 is expanded showing its content
    And Stage 3 is expanded showing its content
    And all collapse icons indicate expanded state

  # Visual Feedback Scenarios

  Scenario: Collapse icon shows hover state when user hovers over it
    Given the user moves their cursor over the Stage 1 collapse icon
    Then the collapse icon displays a hover state

  Scenario: Collapse icon rotates when stage is collapsed
    Given Stage 1 is expanded
    When the user clicks the collapse icon on Stage 1
    Then the collapse icon rotates 90 degrees to point right

  Scenario: Collapse icon rotates back when stage is expanded
    Given Stage 1 is collapsed
    When the user clicks the collapse icon on Stage 1
    Then the collapse icon rotates back to point down

  # Accessibility Scenarios

  Scenario: Collapse icon is keyboard accessible
    Given the user focuses on the Stage 1 collapse icon using keyboard navigation
    When the user presses Enter
    Then Stage 1 content is hidden
    And screen reader announces the collapsed state

  Scenario: Collapse icon has accessible label
    Given the user is using a screen reader
    When the screen reader focuses on a collapse icon
    Then the screen reader announces whether the stage is expanded or collapsed

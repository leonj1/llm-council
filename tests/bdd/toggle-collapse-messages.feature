Feature: Toggle Collapse/Expand Chat Messages
  As a user viewing lengthy chat messages
  I want an icon on each message that allows me to toggle collapsing and expanding
  So that I can reduce scrolling and see an overview of the conversation

  Background:
    Given the user is viewing a conversation with messages

  # Happy Paths

  Scenario: User collapses an expanded user message
    Given a user message is displayed in expanded state
    When the user clicks the collapse icon on that message
    Then the message content is hidden
    And a truncated preview is shown
    And the collapse icon indicates collapsed state

  Scenario: User expands a collapsed user message
    Given a user message is displayed in collapsed state
    When the user clicks the expand icon on that message
    Then the full message content is displayed
    And the collapse icon indicates expanded state

  Scenario: User collapses an expanded assistant message
    Given an assistant message with multiple stages is displayed in expanded state
    When the user clicks the collapse icon on that message
    Then all stages of the assistant message are hidden
    And a collapsed preview placeholder is shown
    And the collapse icon indicates collapsed state

  Scenario: User expands a collapsed assistant message
    Given an assistant message is displayed in collapsed state
    When the user clicks the expand icon on that message
    Then all stages of the assistant message are displayed
    And the collapse icon indicates expanded state

  Scenario: Messages start in expanded state by default
    Given a new message appears in the conversation
    Then the message is displayed in expanded state
    And the collapse icon is visible on the message

  # Edge Cases

  Scenario: Toggle icon visibility on all messages
    Given a conversation with multiple user and assistant messages
    Then each message displays a collapse toggle icon
    And the icons are positioned consistently across all messages

  Scenario: Collapsed preview shows truncated content for user messages
    Given a user message with lengthy content
    When the user collapses that message
    Then a preview of the first portion of the content is shown
    And the preview ends with an ellipsis or indicator

  Scenario: Collapsed preview shows placeholder for assistant messages
    Given an assistant message with multiple stages
    When the user collapses that message
    Then a placeholder text indicating collapsed state is shown

  Scenario: Multiple messages can be collapsed independently
    Given a conversation with three messages
    When the user collapses the first message
    And the user collapses the third message
    Then the first message is collapsed
    And the second message remains expanded
    And the third message is collapsed

  Scenario: Rapid toggling does not cause display issues
    Given a message in expanded state
    When the user clicks the toggle icon multiple times quickly
    Then the message correctly reflects the final toggle state
    And no visual glitches occur

  Scenario: Short messages still show collapse toggle
    Given a user message with very short content
    Then the collapse toggle icon is still visible
    And the user can collapse the message

  # State Behavior

  Scenario: Collapsed state is preserved while navigating within conversation
    Given the user has collapsed a message
    When the user scrolls through the conversation
    Then the collapsed message remains collapsed

  Scenario: Collapsed state resets on page reload
    Given the user has collapsed several messages
    When the user reloads the page
    Then all messages are displayed in expanded state

  Scenario: New messages appear expanded regardless of other collapsed messages
    Given the user has collapsed some messages
    When a new message is added to the conversation
    Then the new message appears in expanded state

  # Loading States

  Scenario: Collapse toggle is disabled during message loading
    Given an assistant message is being loaded
    Then the collapse toggle is not interactive
    Or the collapse toggle is not shown until loading completes

  # Visual Feedback

  Scenario: Collapse icon rotates to indicate state
    Given a message with collapse toggle icon
    When the message is expanded
    Then the icon points downward
    When the message is collapsed
    Then the icon points rightward or sideways

  Scenario: Collapsed preview has distinct visual styling
    Given a collapsed message
    Then the collapsed preview has muted or italicized styling
    And it is visually distinct from expanded content

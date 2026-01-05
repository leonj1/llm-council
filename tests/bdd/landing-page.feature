Feature: Landing Page with Hello World
  As a visitor
  I want to see a landing page when I visit the root URL
  So that I have a welcoming entry point to the application

  Background:
    Given the application is running

  # Happy Paths

  Scenario: Visitor sees Hello World on the landing page
    When the visitor navigates to the root URL
    Then the visitor sees the landing page
    And the landing page displays "Hello World"

  Scenario: Visitor can access the chat page from a different route
    When the visitor navigates to the chat route
    Then the visitor sees the chat interface
    And the chat interface is fully functional

  # Navigation

  Scenario: Landing page is the default page at root URL
    When the visitor opens the application
    Then the browser URL is the root path
    And the landing page is displayed

  Scenario: Chat page is accessible at its dedicated route
    When the visitor navigates directly to the chat route
    Then the browser URL shows the chat path
    And the existing chat functionality is available

  # Preservation of Existing Functionality

  Scenario: Existing chat interface remains intact
    When the visitor accesses the chat page
    Then the sidebar is visible
    And the conversation list is available
    And new conversations can be created

  Scenario: Existing conversation functionality works on chat page
    Given the visitor is on the chat page
    When the visitor creates a new conversation
    Then the conversation appears in the sidebar
    And the visitor can send messages

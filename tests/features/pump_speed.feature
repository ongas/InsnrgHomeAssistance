Feature: Pump speed presets
  As a pool owner
  I want to select pump speed presets in Home Assistant
  So that I can support solar-aware operation

  @status-completed
  Scenario: Show discovered pump speed presets and reported state
    Given a discovered pump speed device with reported presets "Default,1,2,3,4" and current value "Default"
    When the pump speed select is initialized
    Then its options are the reported presets
    And its current option is "Default"
    When discovery reports pump speed "2"
    Then its current option is "2"

  @status-completed
  Scenario: Set a discovered numbered pump speed preset
    Given a discovered pump speed device with reported presets "Default,1,2,3,4" and current value "Default"
    When I select pump speed "2" and polling confirms it
    Then the pump value command is sent for the discovered device
    And the confirmed current option is "2"

  @status-completed
  Scenario: Failed pump speed command does not persist the requested option
    Given a discovered pump speed device with reported presets "Default,1,2,3,4" and current value "Default"
    When I select pump speed "2" and the command fails
    Then the current option remains "Default"

  @status-completed
  Scenario: Unconfirmed pump speed command reverts to reported state
    Given a discovered pump speed device with reported presets "Default,1,2,3,4" and current value "Default"
    When I select pump speed "2" and discovery does not confirm it
    Then the current option remains "Default"

  @status-completed
  Scenario: Missing pump speed device has no guessed state or command
    Given a discovered pump speed device with reported presets "Default,1,2,3,4" and current value "Default"
    When the pump speed device disappears
    Then its current option is unavailable
    And no pump speed command is sent

Feature: Pump speed presets
  As a pool owner
  I want to select pump speed presets in Home Assistant
  So that I can support solar-aware operation

  @status-completed
  Scenario: Pump speed entities exist before data is reported
    Given select platform starts before pump speed is reported
    When the pump speed data remains absent
    Then one unavailable pump speed select and readable status report absent data

  @status-completed
  Scenario: Discovery updates the stable pump speed selector
    Given select platform starts before pump speed is reported
    When discovery reports pump speed presets "Default,1,2" and current value "1" repeatedly
    Then exactly one pump speed select is added with reported options and state
    And pump speed status reports available data

  @status-completed
  Scenario: Failed coordinator refresh has an accurate status
    Given select platform starts before pump speed is reported
    When the coordinator refresh fails
    Then pump speed status reports an update failure

  @status-completed
  Scenario: Unloading select platform has no discovery listener to leak
    Given select platform starts before pump speed is reported
    When the select platform unloads before pump speed discovery
    Then the stable pump speed select was created without a late discovery listener

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
    And no switch command is sent

  @status-completed
  Scenario: Mismatched pump device identifier cannot expose or control another device
    Given pump speed data is keyed as pump speed but reports device identifier "MODE"
    When I select pump speed "ON"
    Then the pump speed selector remains unavailable without guessed options or state
    And no pump or switch command is sent

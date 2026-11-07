Feature: Insnrg integration branding
  As a pool owner
  I want Home Assistant to display recognizable Insnrg branding with an OG badge
  So that I can distinguish my fork from the original integration

  @status-completed
  Scenario: Provide standard local Insnrg brand assets
    Given the Insnrg integration branding assets
    When I inspect the bundled local brand files
    Then square icons and landscape logos are available at standard resolutions

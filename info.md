# Microsoft Teams Presence

Track your Microsoft Teams availability and activity as Home Assistant sensors, using the Microsoft Graph API with MFA-friendly Device Code authentication.

## Sensors

| Sensor | Example states |
|--------|---------------|
| **Availability** | `available`, `busy`, `away`, `do_not_disturb`, `offline` |
| **Activity** | `available`, `in_a_call`, `in_a_meeting`, `presenting`, `away` |
| **Out of Office** | `on` / `off` |

## Setup

1. Install via HACS using the repository URL: `https://github.com/rikdekoning/ha-teams-presence`
2. Restart Home Assistant
3. Go to **Settings -> Devices & Services -> Add Integration** and search for **Microsoft Teams Presence**
4. Open `https://microsoft.com/devicelogin` in your browser, enter the displayed code, and sign in with your Microsoft 365 account — MFA is fully supported
5. Click **Submit** in Home Assistant — your sensors will appear within seconds

> **Corporate accounts:** The integration uses the Microsoft Graph Command Line Tools public client. Some organisations require an admin to grant consent before users can sign in. See the README for details.

## Example automation

```yaml
alias: Teams DND - Turn on light
triggers:
  - trigger: state
    entity_id:
      - sensor.teams_your_name_your_name_teams_activity
conditions:
  - condition: state
    entity_id: sensor.teams_your_name_your_name_teams_activity
    state:
      - do_not_disturb
actions:
  - action: light.turn_on
    target:
      entity_id: light.your_light
mode: single
```

## Privacy

`Presence.Read`, `User.Read`, and `offline_access` scopes are requested. No credentials are stored — authentication uses Microsoft's Device Code flow and tokens are managed by Home Assistant.

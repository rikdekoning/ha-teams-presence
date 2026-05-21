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
3. Go to **Settings → Devices & Services → Add Integration** and search for **Microsoft Teams Presence**
4. Open `https://microsoft.com/devicelogin` in your browser, enter the displayed code, and sign in with your Microsoft 365 account — MFA is fully supported
5. Click **Submit** in Home Assistant — your sensors will appear within seconds

## Example automation

```yaml
automation:
  - alias: "DND light when in Teams call"
    trigger:
      - platform: state
        entity_id: sensor.your_name_teams_activity
        to: "in_a_call"
    action:
      - service: light.turn_on
        target:
          entity_id: light.office_dnd
        data:
          color_name: red
```

## Privacy

Only `Presence.Read` and `offline_access` scopes are requested. No credentials are stored — authentication uses Microsoft's Device Code flow and tokens are managed by Home Assistant.

# ha-teams-presence

Track your Microsoft Teams availability and activity as Home Assistant sensors, using the Microsoft Graph API with MFA-friendly Device Code authentication.

---

## Sensors

| Sensor | Example states |
|--------|---------------|
| `sensor.teams_{name}_{name}_teams_availability` | `available`, `busy`, `away`, `do_not_disturb`, `offline` |
| `sensor.teams_{name}_{name}_teams_activity` | `available`, `in_a_call`, `in_a_meeting`, `presenting`, `away` |
| `sensor.teams_{name}_{name}_teams_out_of_office` | `on` / `off` |

All sensors expose additional attributes such as the raw API value, color hint, user email, and (for out-of-office) the OOO message.

---

## Requirements

- Home Assistant 2023.1.0 or newer
- A Microsoft 365 account with Teams
- [HACS](https://hacs.xyz) installed in Home Assistant

---

## Installation via HACS

1. Open HACS in Home Assistant
2. Go to **Integrations -> three dots menu -> Custom Repositories**
3. Enter the repository URL:
   ```
   https://github.com/rikdekoning/ha-teams-presence
   ```
   and set the category to **Integration**, then click **Add**
4. Search for **Microsoft Teams Presence** in HACS and click **Download**
5. Restart Home Assistant

---

## Setup

1. Go to **Settings -> Devices & Services -> Add Integration**
2. Search for **Microsoft Teams Presence** and select it
3. A screen will appear showing a short code and a URL:
   - Open [https://microsoft.com/devicelogin](https://microsoft.com/devicelogin) in your browser
   - Enter the code shown in Home Assistant
   - Sign in with your Microsoft 365 account — MFA, Authenticator, and passkeys are all fully supported
4. Return to Home Assistant and click **Submit**
5. Your three presence sensors will appear within seconds

> Tokens are stored securely in Home Assistant and refresh automatically. You will not need to sign in again unless you explicitly revoke access.

---

## Automations

Replace `sensor.teams_your_name_your_name_teams_activity` with your actual entity ID, which you can find under **Settings -> Devices & Services -> Microsoft Teams Presence**.

### Turn on a light when in Do Not Disturb

```yaml
alias: Teams DND - Turn on light
description: ""
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
    data: {}
mode: single
```

### Turn off the light when no longer in Do Not Disturb

```yaml
alias: Teams DND - Turn off light
description: ""
triggers:
  - trigger: state
    entity_id:
      - sensor.teams_your_name_your_name_teams_activity
conditions:
  - condition: not
    conditions:
      - condition: state
        entity_id: sensor.teams_your_name_your_name_teams_activity
        state:
          - do_not_disturb
actions:
  - action: light.turn_off
    target:
      entity_id: light.your_light
    data: {}
mode: single
```

### Turn on a light when in a call or meeting

```yaml
alias: Teams - Light on when in call or meeting
description: ""
triggers:
  - trigger: state
    entity_id:
      - sensor.teams_your_name_your_name_teams_activity
conditions:
  - condition: state
    entity_id: sensor.teams_your_name_your_name_teams_activity
    state:
      - in_a_call
      - in_a_conference_call
      - in_a_meeting
actions:
  - action: light.turn_on
    target:
      entity_id: light.your_light
    data: {}
mode: single
```

### Notify when out of office is active

```yaml
alias: Teams - Notify when Out of Office
description: ""
triggers:
  - trigger: state
    entity_id:
      - sensor.teams_your_name_your_name_teams_out_of_office
    to: "on"
conditions: []
actions:
  - action: notify.mobile_app_your_phone
    data:
      message: You are marked as Out of Office in Teams
mode: single
```

---

## Availability states

| State | Meaning |
|-------|---------|
| `available` | Online and available |
| `available_idle` | Available but idle |
| `away` | Away |
| `be_right_back` | Be right back |
| `busy` | Busy |
| `busy_idle` | Busy but idle |
| `do_not_disturb` | Do not disturb |
| `offline` | Offline |
| `unknown` | Presence unknown |

## Activity states

| State | Meaning |
|-------|---------|
| `available` | Available |
| `away` | Away |
| `be_right_back` | Be right back |
| `busy` | Busy |
| `do_not_disturb` | Do not disturb |
| `in_a_call` | In a 1:1 call |
| `in_a_conference_call` | In a conference call |
| `inactive` | Inactive |
| `in_a_meeting` | In a meeting |
| `offline` | Offline |
| `off_work` | Off work |
| `out_of_office` | Out of office |
| `presenting` | Presenting |
| `urgent_interruptions_only` | Urgent interruptions only |
| `unknown` | Unknown |

---

## Privacy & permissions

The integration requests the following delegated scopes from Microsoft:

- `Presence.Read` — read your own Teams presence status
- `User.Read` — read your basic profile (display name and email, used to name the sensors)
- `offline_access` — allow background token refresh without re-signing in

No credentials are ever stored. Authentication uses Microsoft's Device Code flow — your password never touches Home Assistant. Tokens are saved securely in Home Assistant's config entry storage.

No app registration is required — the integration uses the well-known Microsoft Graph Command Line Tools public client, so any Microsoft 365 user can sign in without needing Azure admin permissions.

---

## Polling interval

Presence is refreshed every **30 seconds** by default. This balances responsiveness with Microsoft Graph API rate limits (Teams itself updates presence approximately every 5 seconds, but the Graph API is best polled no more than once per 30s for home use).

To change the interval, edit `UPDATE_INTERVAL` in `const.py` before installing.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Still waiting" after signing in | Wait 5-10 seconds and click Submit again |
| Sensor shows `unknown` | Check HA logs for Graph API errors; re-authenticate via the integration settings |
| MFA prompt does not appear | Open the link in a private/incognito browser window |
| Integration not found in HACS | Ensure the custom repository was added with category set to **Integration** |
| Sensors disappear after a while | Your refresh token may have expired — remove and re-add the integration |
| No states visible in automation editor | Wait 30 seconds for the sensor to poll and report its first value |

---

## Contributing

Pull requests are welcome. Please open an issue first for major changes.

## License

MIT

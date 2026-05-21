"""Constants for the Microsoft Teams Presence integration."""

DOMAIN = "teams_presence"
PLATFORMS = ["sensor"]

# Microsoft Graph Command Line Tools - well-known public client
CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["https://graph.microsoft.com/Presence.Read", "https://graph.microsoft.com/User.Read", "offline_access"]

# Graph API
GRAPH_PRESENCE_URL = "https://graph.microsoft.com/v1.0/me/presence"

# Polling interval in seconds
UPDATE_INTERVAL = 30

# Config entry keys
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_TOKEN_EXPIRY = "token_expiry"
CONF_USER_DISPLAY_NAME = "user_display_name"
CONF_USER_EMAIL = "user_email"

# Presence availability states (from Microsoft Graph)
AVAILABILITY_STATES = {
    "Available": "available",
    "AvailableIdle": "available_idle",
    "Away": "away",
    "BeRightBack": "be_right_back",
    "Busy": "busy",
    "BusyIdle": "busy_idle",
    "DoNotDisturb": "do_not_disturb",
    "Offline": "offline",
    "PresenceUnknown": "unknown",
}

# Presence activity states
ACTIVITY_STATES = {
    "Available": "available",
    "Away": "away",
    "BeRightBack": "be_right_back",
    "Busy": "busy",
    "DoNotDisturb": "do_not_disturb",
    "InACall": "in_a_call",
    "InAConferenceCall": "in_a_conference_call",
    "Inactive": "inactive",
    "InAMeeting": "in_a_meeting",
    "Offline": "offline",
    "OffWork": "off_work",
    "OutOfOffice": "out_of_office",
    "PresenceUnknown": "unknown",
    "Presenting": "presenting",
    "UrgentInterruptionsOnly": "urgent_interruptions_only",
}

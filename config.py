"""
PhoneKeyboardBridge - config.py
Edit the values below to match your build / release / branding.
"""

APP_NAME = "Phone Keyboard Bridge"          # shown in About/Help/tray/title bar
APP_VERSION = "1.0.0"
DEVELOPER_NAME = "Pixel Forge Studio"
DEVELOPER_WEBSITE = "https://pixelforgestudioprabhath.netlify.app/"
TERMS_URL = "https://termsandconditionsa.netlify.app/"

# GitHub release used to download "core assets" (images/icons/etc.) on first run.
# The release must contain a single asset named ASSETS_ZIP_NAME.
GITHUB_OWNER = "your-github-username"
GITHUB_REPO = "your-repo-name"
ASSETS_ZIP_NAME = "core_assets.zip"

# Local folder where the downloaded assets get extracted (relative to app data dir)
ASSETS_FOLDER_NAME = "assets"

# LAN server
LAN_HTTP_PORT = 8743
PIN_LENGTH = 6

# Loading screen custom text (edit freely)
LOADING_TITLE = "PhoneKeyboardBridge"
LOADING_SUBTITLE = "Use your phone as a wireless PC keyboard — no app required"
LOADING_DEV_LINE = f"Developed by {DEVELOPER_NAME}"

# Ads / promo area shown at the bottom of the main window
PROMO_URL = "https://pixeladsapp.netlify.app/"

# VERSION 6.2

# Change the version if you do an update:
# - Major version number for intended changes
# - Minor version number for fixing typos etc.
keys = {
    "DJANGO": {
        "LOCAL": "TEST",
        "PRODUCTION": "",
        "SANDBOX": "",
        "POSTGRES": "",
        "SMTP": ""
    },
    "DROPBOX": {
        "APP_KEY": "TEST_ID",
        "APP_SECRET": "TEST_KEY",
    },
    "FACEBOOK": {
        "www.example.com": {
            "APP_ID": "TEST_ID",
            "APP_SECRET": "TEST_KEY"
        },
        "WEBHOOK_CHALLENGE": ""
    },
    "GITHUB": {
        "CLIENT_ID": "TEST_ID",
        "CLIENT_SECRET": "TEST_KEY"
    },
    "GMAIL": {
        "APP_KEY": "TEST_ID",
        "APP_SECRET": "TEST_KEY"
    },
    "INSTAGRAM": {
        "CLIENT_ID": "TEST_ID",
        "CLIENT_SECRET": "TEST_KEY"
    },
    "TWITTER": {
        "APP_KEY": "TEST_ID",
        "APP_SECRET": "TEST_KEY"
    },
    "reCaptcha": {
        "SITE_KEY": "",
        "SECRET_KEY": ""
    }
}
# Generate secrets with:
# cat /dev/urandom | tr -dc 'a-zA-Z0-9-_!@#$%^&*()_+{}|:<>?=' | fold -w 64 | head -n 1


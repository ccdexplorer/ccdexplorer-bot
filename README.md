[![Publish DockerHub image](https://github.com/ccdexplorer/ccdexplorer-site/actions/workflows/build-push.yml/badge.svg)](https://github.com/ccdexplorer/ccdexplorer-site/actions/workflows/build-push.yml)

# CCDExplorer Bot

The bot. Rewritten three times. 

### Install and Run
0. Git clone, make a venv (`python3 -m venv .venv`) and activate it. 
1. Install dependencies (in the venv)
```zsh
pip install -r requirements.txt
```
3. Set ENV variables
```
NOTIFIER_API_TOKEN (API token for notifier bot)
API_TOKEN (API token for actual bot)
FASTMAIL_TOKEN (I use Fastmail to send email, leave blank, won't send email)
MONGO_URI (MongoDB URI)
ADMIN_CHAT_ID (Telegram admin chat ID)
MAILTO_LINK (I use Fastmail to send email, leave blank, won't send email)
MAILTO_USER (I use Fastmail to send email, leave blank, won't send email)
GRPC_MAINNET (A list of dicts with GPRC hosts) (Example: [{"host": "localhost", "port": 20000}, {"host": "my.validator.com", "port": 20000}])
GRPC_TESTNET (Same as GPRC_MAINNET)
```

### Run Tests
All notification types should have a corresponding test. 
Use `pytest` to test these. 

## Deployment
A Dockerfile is supplied that builds the project into a Docker image (this is the image that is being used on the CCDExplorer Bot).

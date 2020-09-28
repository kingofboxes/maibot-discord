# maibot-discord
Maimai DX+ Discord Bot: Side project for Discord bot which connects to maimai DX NET and collects user records and history.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Only prerequisites required is Python 3.6+, with pip3 installed.

### Installing

Below is a step-by-step guide on setting up the program to get a development environment running.

1. Clone this repo.

```
git clone git@github.com:kingofboxes/maibot-discord.git
```

2. Change directory to of the cloned repo and create a new virtual environment.

```
cd maibot-discord
python3 -m venv .venv
```

3. Activate the virtual environment.

```
. .venv/bin/activate
```

4. Install the requirements using pip3.

```
pip3 install -r requirements.txt
```

5. Create a new file called '.env' as follows.

```
touch .env
```

6. Add the following lines:

```
DISCORD_TOKEN=
MONGO_USR = 
MONGO_PWD = 
MONGO_HOSTNAME = 
MONGO_PORT = 
```

7. Run the program.

```
./start.py
```

8. If done correctly, it should say that your bot has connected.

## Current Features

### Features List
1. User profile. `!user` will send a Discord embed of your maimai DX NET profile in the channel.
2. Search. `!search songname` will search the records for a song that you've played in the past.
3. Recents. `!recent n (1 <= n <= 50)` will display the n-th latest song that you've played. 'n' is optional, but if not specified, returns latest track played.

### Login System
1. Use `!map segaid` to map your Discord ID to a SEGA ID.
2. Use `!password password` to log in to your maimai DX NET profile.

Your password is not stored anywhere on the bot. The cookie is saved and reused for future logins when the session expires.
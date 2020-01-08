# image-bot

bot is created by catzoo

To use this bot, create a ``.env`` file with these values:
```
TOKEN=<bot token>
DATA=<data directory>
DEBUG=<boolean>
DEBUG_ID=<debug user. Can be multiple, seperate with ','>
GUILD=<guild's id>
TIME=<time>
TIME_EVERY=<time_every>
```
``TIME`` / ``TIME_EVERY`` will be used to determine the next image to send. There are two modes this supports.
These two modes will look at TIME and TIME_EVERY differently.

### Mode 1
-   This is for a specific time of the day. For example, in this mode you can have it only send it at
    5:30 pm per day
-   To set this mode do:
    - ``TIME=Minute,Second``
    - ``TIME_EVERY=Hour,Minute``
    - For example, to set it to send an image every hour and have it start at 0:30:00, do:
    ```
    TIME=30,0
    TIME_EVERY=1,0
    ```

### Mode 2 
-   This is for sending it constantly. For example, in this mode you can have it start sending an image every hour rather than per day.
-   To set this mode do:
    - ``TIME=Hour,Minute`` - note it will be in 24 hours
    - ``Do not put in a TIME_EVERY``
    - For example, to have it send at every 5:30 pm, do:
    ```
    TIME=17,30
    ```


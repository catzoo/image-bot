import os
from pathlib import Path
from dotenv import load_dotenv


class EnvError(Exception):
    """
    Custom env exception.
    Gets raised whenever there is
    any .env errors.
    """
    pass


# Loading and checking the .env file
env_file = Path(".env")

if not env_file.is_file():
    raise EnvError('cannot find .env file!')

load_dotenv()
token = os.getenv('TOKEN')
debug = os.getenv('DEBUG')
debug_id = os.getenv('DEBUG_ID')
data_folder = os.getenv('DATA')
main_guild = os.getenv('GUILD')
image_time = os.getenv('TIME')
image_time_every = os.getenv('TIME_EVERY')

if token is None:
    raise EnvError('Missing TOKEN value!')
if debug is None:
    raise EnvError('Missing DEBUG value!')
if data_folder is None:
    raise EnvError('Missing DATA value!')
if debug_id is None:
    raise EnvError('Missing DEBUG_ID value!')
else:
    try:
        temp_list = []
        debug_id = debug_id.split(',')
        for x in debug_id:
            temp_list.append(int(x))
        debug_id = temp_list
    except ValueError:
        raise EnvError('DEBUG_ID has to be a number!')

if main_guild is None:
    raise EnvError('Missing GUILD value!')
else:
    try:
        main_guild = int(main_guild)
    except ValueError:
        raise EnvError('GUILD has to be a number')

if debug == 'False' or debug == 'false':
    debug = False
elif debug == 'True' or 'true':
    debug = True
else:
    raise EnvError("DEBUG value has to be 'true' or 'false'")

if image_time:
    image_time = image_time.split(',')
    temporary = []
    try:
        for x in image_time:
            temporary.append(int(x))

        image_time = list(temporary)
    except ValueError:
        raise EnvError('TIME has to be an integer')

if image_time_every:
    image_time_every = image_time_every.split(',')
    temporary = []
    try:
        for x in image_time_every:
            temporary.append(int(x))

        image_time_every = list(temporary)
    except ValueError:
        raise EnvError('TIME_EVERY has to be an integer')

# make the directory if it doesn't exist
if not Path(data_folder).is_dir():
    os.mkdir(data_folder)

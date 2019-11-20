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
data_folder = os.getenv('DATA')
main_guild = os.getenv('GUILD')

if token is None:
    raise EnvError('Missing TOKEN value!')
if debug is None:
    raise EnvError('Missing DEBUG value!')
if data_folder is None:
    raise EnvError('Missing DATA value!')
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

# make the directory if it doesn't exist
if not Path(data_folder).is_dir():
    os.mkdir(data_folder)

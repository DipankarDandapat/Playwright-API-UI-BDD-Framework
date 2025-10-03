import json
from pathlib import Path
from utils import logger

log = logger.customLogger()

def read_file(folder_name, file_name):
    path = get_file_with_json_extension(folder_name, file_name)
    try:
        with path.open(mode='r') as f:
            data = json.load(f)
            # log.info(f"Successfully read data from file: {file_name}")
            return data
    except FileNotFoundError:
        log.error(f"File not found: {path}")
        raise
    except json.JSONDecodeError as e:
        log.error(f"Error decoding JSON from file: {path}. Error: {e}")
        raise
    except Exception as e:
        log.error(f"An unexpected error occurred while reading file: {path}. Error: {e}")
        raise

def get_file_with_json_extension(folder_name, file_name):
    base_path = Path.cwd().joinpath('testdata')
    if '.json' in file_name:
        path = base_path.joinpath(folder_name, file_name)
    else:
        path = base_path.joinpath(folder_name, f'{file_name}.json')
    # log.info(f"Resolved file path: {path}")
    return path
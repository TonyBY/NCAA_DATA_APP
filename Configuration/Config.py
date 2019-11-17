from getpass import getpass
import cmd
import yaml

def parse_config_input(config_filename):
    cfg = {}
    with open(config_filename, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        cfg['DB_USER'] = input("Oracle User Name:")
        cfg['DB_PASSWORD'] = getpass("Oracle Pass Word:")
    return cfg
import os
from typing import Dict, List, Union

import wandb
import yaml

from deepreg import log
from deepreg.config.v011 import parse_v011

logger = log.get(__name__)


def update_nested_dict(d: Dict, u: Dict) -> Dict:
    """
    Merge two dicts.

    https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    :param d: dict to be overwritten in case of conflicts.
    :param u: dict to be merged into d.
    :return:
    """

    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update_nested_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def load_configs(config_path: Union[str, List[str]]) -> Dict:
    """
    Load multiple configs and update the nested dictionary.

    :param config_path: list of paths or one path.
    :return: the loaded config
    """
    if isinstance(config_path, str):
        config_path = [config_path]
    # replace ~ with user home path
    config_path = [os.path.expanduser(x) for x in config_path]
    config: Dict = {}
    for config_path_i in config_path:
        with open(config_path_i) as file:
            config_i = yaml.load(file, Loader=yaml.FullLoader)
        config = update_nested_dict(d=config, u=config_i)
    loaded_config = config_sanity_check(config)

    if loaded_config != config:
        # config got updated
        head, tail = os.path.split(config_path[0])
        filename = "updated_" + tail
        save(config=loaded_config, out_dir=head, filename=filename)
        logger.error(
            "The provided configuration file is outdated. "
            "An updated version has been saved at %s.",
            os.path.join(head, filename),
        )

    return loaded_config


def save(config: dict, out_dir: str, filename: str = "config.yaml"):
    """
    Save the config into a yaml file.

    :param config: configuration to be outputed
    :param out_dir: directory of the output file
    :param filename: name of the output file
    """
    assert filename.endswith(".yaml")
    with open(os.path.join(out_dir, filename), "w+") as f:
        f.write(yaml.dump(config))


def config_sanity_check(config: dict) -> dict:
    """
    Check if the given config satisfies the requirements.

    :param config: entire config.
    """

    # back compatibility support
    config = parse_v011(config)

    # check model
    if config["train"]["method"] == "conditional":
        if config["dataset"]["train"]["labeled"] is False:  # unlabeled
            raise ValueError(
                "For conditional model, data have to be labeled, got unlabeled data."
            )

    return config


def has_wandb_callback(config: dict):
    """
    Function that checks if a given config has W&B
    keys.
    :param config: config dictionary with parameters for run.
    :return: bool, whether wandb key in config.
    """
    if "wandb" in config:
        return True
    return False


def instantiate_wandb_run(config: dict):
    """
    From a config dictionary with wandb keys,
    run wandb.init to log training.

    :param config: config dictionary with parameters for run.
    :return: N/A.
    """
    if "init" not in config["wandb"]:
        logging.error("No init field in config. Creating empty init.")
        wandb.init()
    else:
        wandb_init = config["wandb"]["init"]
        wandb.init(**wandb_init)


def instantiate_wandb_callback(config: dict):
    """
    From a config dictionary with wandb keys,
    generate a run callback to use during training.

    :param config: config dictionary with parameters for run.
    :return: tf.keras.callback, see W&B docs for more info.
    """
    # If the callback key does not exist, initialise an
    # empty run.
    if "callback" not in config["wandb"]:
        logging.error("No callback field in config. Creating empty callback.")
        wandb_callback = wandb.keras.WandbCallback()
    # Get sub dict that contains the wandb params
    else:
        wandb_dict = config["wandb"]["callback"]
        wandb_callback = wandb.keras.WandbCallback(**wandb_dict)
    return wandb_callback

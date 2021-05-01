"""Bot for GALAH."""

import argparse
import json
import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from random import choice

import numpy as np
from astropy.io import fits

from do_the_tweeting import tweet
from get_images import get_hips_image
from plot_spectra import plot_spectra
from plot_stellar_params import plot_stellar_params


def get_keys(secrets_path):
    """Loads the JSON file of secrets."""
    with open(secrets_path) as f:
        return json.load(f)


def get_secrets(cwd, logger):
    SECRETS_FILE = Path.joinpath(cwd, '.secret/twitter_secrets.json')
    logger.debug("Getting the Twitter secrets from %s", SECRETS_FILE)
    try:
        keys = get_keys(SECRETS_FILE)
        return keys
    except FileNotFoundError as e:
        logger.error(e)
        logger.error("Did not load secrets file. Quitting.")
        sys.exit("Did not load secrets file. Quitting.")


def main():
    cwd = Path(__file__).parent
    config_file = Path.joinpath(cwd, 'logging.conf')
    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger('robot_galah')
    logger.info("STARTING")

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sobject_id",
                        help="Tweet a specific sobject_id.",
                        type=int)
    group.add_argument("--dr3_source_id",
                        help="Tweet a specific dr3_source_id.",
                        type=int)
    parser.add_argument("--dry_run",
                        help="Do everything but tweet.",
                        action="store_true")
    args = parser.parse_args()
    sobject_id_arg = args.sobject_id
    DRY_RUN = args.dry_run
    dr3_source_id_arg = args.dr3_source_id

    tweet_content_dir = Path.joinpath(cwd, "tweet_content/.")
    logger.debug(
        "Deleting the old files in %s if they exist", tweet_content_dir.as_posix())
    for f in tweet_content_dir.iterdir():
        if f.is_file:
            logger.debug("Deleting %s", f.name)
            f.unlink()

    secrets_dict = get_secrets(cwd, logger)
    # from matplotlib.offsetbox import AnchoredText
    DATA_DIR = secrets_dict["DATA_DIR"]
    DATA_FILE = "GALAH_DR3_main_allstar_ages_dynamics_bstep_v2.fits"

    BIRD_WORDS = ['squawk', 'chirp', 'tweet', 'hoot', 'cacaw', 'quack',
                  'cluck', 'screech', 'coo', 'warble', 'honk']

    galah_dr3 = fits.open(f"{DATA_DIR}/{DATA_FILE}")[1].data

    basest_idx_galah = ((galah_dr3['flag_sp'] == 0) &
                        (galah_dr3['flag_fe_h'] == 0) &
                        (galah_dr3['snr_c3_iraf'] > 30))

    survey_str = {"galah_main": "during the main GALAH survey",
                  "galah_faint": "during the main GALAH survey",
                  "k2_hermes": "during the K2-HERMES survey",
                  "tess_hermes": "during the TESS-HERMES survey",
                  "other": "during a special observing programme", }

    if (sobject_id_arg is not None):
        logger.info("Told to do a specific star: sobject_id=%s",
                    sobject_id_arg)
        star_idx = galah_dr3['sobject_id'] == sobject_id_arg
        if not np.any(star_idx):
            logger.error("Not a valid sobject_id. Quitting.")
            sys.exit("Not a valid sobject_id. Quitting.")
        the_star = galah_dr3[star_idx][0]
    elif (dr3_source_id_arg is not None):
        logger.info("Told to do a specific star: dr3_source_id=%s",
                    dr3_source_id_arg)
        star_idx = galah_dr3['dr3_source_id'] == dr3_source_id_arg
        if not np.any(star_idx):
            logger.error("Not a valid dr3_source_id. Quitting.")
            sys.exit("Not a valid dr3_source_id. Quitting.")
        the_star = galah_dr3[star_idx][0]
    else:
        USEFUL_STAR = False
        while USEFUL_STAR is False:
            rand_idx = np.random.randint(low=0, high=len(galah_dr3))
            logger.debug("Trying index %i", rand_idx)
            the_star = galah_dr3[rand_idx]
            if ((the_star['flag_sp'] == 0) &
                (the_star['flag_fe_h'] == 0) &
                    (the_star['snr_c3_iraf'] > 30)):
                USEFUL_STAR = True
                logger.info("Found a useful star: %s", the_star['sobject_id'])

    logger.debug("Extracting the useful information about the star")
    gaia_dr3_id = the_star['dr3_source_id']
    YYMMDD = str(the_star['sobject_id'])[:6]
    d = datetime.strptime(YYMMDD, "%y%m%d").date()
    obs_date_str = d.strftime('%-d %b %Y')
    survey_name = the_star['survey_name']
    age = the_star['age_bstep']
    mass = the_star['m_act_bstep']
    distance = the_star['distance_bstep']

    logger.info("Creating the tweet text:")
    tweet_line_1 = f"{choice(BIRD_WORDS).upper()}!"
    tweet_line_2 = f"We observed Gaia eDR3 {gaia_dr3_id} on the night of {obs_date_str} {survey_str[survey_name]}."
    tweet_line_3 = f"It is about {np.round(distance*10)*100:0.0f} pc from the Sun, and we estimate this star is {age:0.0f} Gyr old and {mass:0.1f} solar masses."
    tweet_text = "\n\n".join([tweet_line_1, tweet_line_2, tweet_line_3])

    for line in [tweet_line_1, tweet_line_2, tweet_line_3]:
        logger.info(line)
    plot_stellar_params(galah_dr3, the_star, basest_idx_galah)
    hips_survey = get_hips_image(the_star, secrets_dict)
    plot_spectra(the_star)
    if not DRY_RUN:
        tweet(tweet_text, hips_survey, gaia_dr3_id, secrets_dict)

if __name__ == "__main__":
    main()

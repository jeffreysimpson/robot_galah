"""Bot for GALAH."""

import logging
import logging.config
from datetime import datetime
from os.path import dirname, join
from pathlib import Path
from random import choice

import numpy as np
from astropy.io import fits

from do_the_tweeting import tweet
from get_images import get_hips_image
from plot_spectra import plot_spectra
from plot_stellar_params import plot_stellar_params


def main():
    cwd = Path.cwd()
    config_file = Path.joinpath(cwd, 'logging.conf')
    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger('robot_galah')

    logger.info("STARTING")

    tweet_content_dir = Path.joinpath(cwd, "tweet_content/.")
    logger.debug(
        f"Deleting the old files in {tweet_content_dir.as_posix()} if they exist")
    for f in tweet_content_dir.iterdir():
        if f.is_file:
            logger.debug(f"Deleting {f.name}")
            f.unlink()

    # from matplotlib.offsetbox import AnchoredText
    DATA_DIR = "/Users/jeffreysimpson/ownCloud/galah_catalogues/dr3"
    DATA_FILE = "GALAH_DR3_main_allstar_ages_dynamics_bstep_v2.fits"

    BIRD_WORDS = ['squawk', 'chirp', 'tweet', 'hoot',
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

    USEFUL_STAR = False
    while USEFUL_STAR is False:
        rand_idx = np.random.randint(low=0, high=len(galah_dr3))
        logger.debug(f"Trying index {rand_idx}")
        the_star = galah_dr3[rand_idx]
        if ((the_star['flag_sp'] == 0) &
            (the_star['flag_fe_h'] == 0) &
                (the_star['snr_c3_iraf'] > 30)):
            USEFUL_STAR = True
            logger.info(f"Found a useful star: {the_star['sobject_id']}")

    logger.debug("Extracting the useful information about the star")
    gaia_dr3_id = the_star['dr3_source_id']
    star_id = the_star['star_id']
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

    if plot_stellar_params(galah_dr3, the_star, basest_idx_galah) == 1:
        logger.error("Did not complete the plots properly. Quitting!")
        return 1
    hips_survey = get_hips_image(the_star)
    if hips_survey == 1:
        logger.error("Did not download a sky image. Quitting!")
        return 1
    if plot_spectra(the_star) == 1:
        logger.error("Unable to download the spectra. Quitting!")
        return 1
    if tweet(tweet_text, hips_survey, gaia_dr3_id) == 1:
        logger.error("Did not tweet. Quitting!")


if __name__ == "__main__":
    main()

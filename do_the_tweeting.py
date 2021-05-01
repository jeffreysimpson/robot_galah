

import logging
import logging.config
from pathlib import Path

import numpy as np
import tweepy
from tweepy.error import TweepError




def media_load(filename, alt_text, api, logger):
    """Load the images and gets the media IDs for Twitter."""
    logger.info("Getting media_id for %s", filename)
    try:
        with open(filename, 'rb') as file:
            media = api.media_upload(filename=filename, file=file)
    except FileNotFoundError as e:
        logger.error(e)
        return ""
    except TweepError as e:
        logger.error(e)
        return ""
    api.create_media_metadata(media.media_id_string, alt_text)
    logger.debug("The media_id for %s is %s", filename, media.media_id_string)
    return media.media_id_string


def tweet(tweet_text, hips_survey, gaia_dr3_id, secrets_dict):

    cwd = Path(__file__).parent

    tweet_content_dir = Path.joinpath(cwd, "tweet_content")
    config_file = Path.joinpath(cwd, 'logging.conf')

    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger('do_the_tweeting')

    alt_text_dict = {"sky_image_overlay.jpg": f"A 15 by 15 arcminute image from the {hips_survey}. Gaia eDR3 {gaia_dr3_id} is found at the centre.",
                     "stellar_params_teff.png": f"Two graphs made from GALAH survey data. The top panel is a temperature versus surface gravity, and the bottom panel is the Tinsley-Wallerstein diagram showing the metallicity versus the alpha abundance. On both, Gaia eDR3 {gaia_dr3_id} is indicated with a big red star.",
                     "stellar_params_L_Z.png": f"Two graphs made from GALAH survey data. The top panel is the z-component of the angular momentum versus the orbital energy. The bottom panel is the Toomre diagram. On both, Gaia eDR3 {gaia_dr3_id} is indicated with a big red star.",
                     "spectra.png": f"The normalized HERMES spectrum of Gaia eDR3 {gaia_dr3_id}. HERMES acquires the spectrum of the star in four non-contiguous wavelength regions: Blue, Green, Red, and Infrared."}

    auth = tweepy.OAuthHandler(
        secrets_dict['consumer_key'], secrets_dict['consumer_secret'])
    auth.set_access_token(secrets_dict['key'], secrets_dict['secret'])

    api = tweepy.API(auth)

    media_id = [media_load(Path.joinpath(tweet_content_dir, filename), alt_text, api, logger)
                for filename, alt_text in alt_text_dict.items()]
    if np.any([m == "" for m in media_id]):
        logger.error(
            "Missing a media_id values for %i images.", np.sum([m == '' for m in media_id]))
        return 1
    try:
        tweet_return = api.update_status(status=tweet_text, media_ids=media_id)
    except TweepError as e:
        logger.error(e)
        return 1
    logger.info(
        "Tweet link: %s", tweet_return.entities['urls'][0]['expanded_url'])
    return 0

import json

import tweepy

import logging
import logging.config
import numpy as np

from tweepy.error import TweepError


def get_keys(path):
    """Loads the JSON file of secrets."""
    with open(path) as f:
        return json.load(f)


def media_load(filename, alt_text, api, logger):
    """Load the images and gets the media IDs for Twitter."""
    logger.info(f"Getting media_id for {filename}")
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
    logger.debug(f"The media_id for {filename} is {media.media_id_string}")
    return media.media_id_string


def tweet(tweet_text, hips_survey, star_id):

    SECRETS_FILE = ".secret/twitter_secrets.json"
    logging.config.fileConfig('logging.conf')
    # create logger
    logger = logging.getLogger('do_the_tweeting')

    logger.debug(f"Getting the Twitter secrets from {SECRETS_FILE}")
    keys = get_keys(SECRETS_FILE)

    alt_text_dict = {"sky_image_overlay.jpg": f"A 15 by 15 arcminute image from the {hips_survey.split('/')[2]}. {star_id} is found at the centre.",
                     "stellar_params_teff.png": f"Two graphs made from GALAH survey data. The top panel is a temperature versus surface gravity, and the bottom panel is the Tinsley-Wallerstein diagram showing the metallicity versus the alpha abundance. On both, {star_id} is indicated with a big red star.",
                     "stellar_params_L_Z.png": f"Two graphs made from GALAH survey data. The top panel is the z-component of the angular momentum versus the orbital energy. The bottom panel is the Toomre diagram. On both, {star_id} is indicated with a big red star.",
                     "spectra.png": f"The normalized HERMES spectrum of {star_id}. HERMES acquires the spectrum of the star in four non-contiguous wavelength regions: Blue, Green, Red, and Infrared.",}

    auth = tweepy.OAuthHandler(keys['consumer_key'], keys['consumer_secret'])
    auth.set_access_token(keys['key'], keys['secret'])

    api = tweepy.API(auth)

    media_id = [media_load(f"tweet_content/{filename}", alt_text, api, logger)
                for filename, alt_text in alt_text_dict.items()]
    if np.any([m == "" for m in media_id]):
        logger.error(
            f"Missing a media_id values for {np.sum([m == '' for m in media_id])} images.")
        return 1
    try:
        tweet_return = api.update_status(status=tweet_text, media_ids=media_id)
    except TweepError as e:
        logger.error(e)
        return 1
    logger.info(
        f"Tweeted at {tweet_return.entities['urls'][0]['expanded_url']}")

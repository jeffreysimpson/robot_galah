import logging
import logging.config
import sys
from pathlib import Path

import tweepy
from tweepy.error import TweepError


def media_load(filename, alt_text, api, logger):
    """Load the images and gets the media IDs for Twitter."""
    logger.info("Getting media_id for %s", filename)
    try:
        with open(filename, "rb") as file:
            media = api.media_upload(filename=filename, file=file)
    except FileNotFoundError as e:
        logger.error(e)
        logger.error("Image to tweet does not exist. Quitting.")
        sys.exit("Image to tweet does not exist. Quitting.")
    except TweepError as e:
        logger.error(e)
        logger.error("Twitter didn't like the image? Quitting.")
        sys.exit("Twitter didn't like the image? Quitting.")
    api.create_media_metadata(media.media_id_string, alt_text)
    logger.debug("The media_id for %s is %s", filename, media.media_id_string)
    return media.media_id_string


def tweet(tweet_text, hips_survey, BEST_NAME, secrets_dict, DRY_RUN=False):

    cwd = Path(__file__).parent

    tweet_content_dir = Path.joinpath(cwd, "tweet_content")
    config_file = Path.joinpath(cwd, "logging.conf")

    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger("do_the_tweeting")

    alt_text_dict = {
        "sky_image_overlay.jpg": f"A 15 by 15 arcminute image from the {hips_survey}. {BEST_NAME} is found at the centre.",
        "stellar_params_teff.png": f"Two graphs made from GALAH survey data. The top panel is a temperature versus surface gravity, and the bottom panel is the Tinsley-Wallerstein diagram showing the metallicity versus the alpha abundance. On both, {BEST_NAME} is indicated with a big red star.",
        "stellar_params_L_Z.png": f"Two graphs made from GALAH survey data. The top panel is the z-component of the angular momentum versus the orbital energy. The bottom panel is the Toomre diagram. On both, {BEST_NAME} is indicated with a big red star.",
        "spectra.png": f"The normalized HERMES spectrum of {BEST_NAME}. HERMES acquires the spectrum of the star in four non-contiguous wavelength regions: Blue, Green, Red, and Infrared.",
    }

    auth = tweepy.OAuthHandler(
        secrets_dict["consumer_key"], secrets_dict["consumer_secret"]
    )
    auth.set_access_token(secrets_dict["key"], secrets_dict["secret"])

    api = tweepy.API(auth)

    media_id = [
        media_load(Path.joinpath(tweet_content_dir, filename), alt_text, api, logger)
        for filename, alt_text in alt_text_dict.items()
    ]
    try:
        if not DRY_RUN:
            tweet_return = api.update_status(status=tweet_text, media_ids=media_id)
            logger.info(
                "Tweet link: %s", tweet_return.entities["urls"][0]["expanded_url"]
            )
        else:
            logger.info("Only a dry run, so not tweeting.")
        sys.exit()
    except TweepError as e:
        logger.error(e)
        logger.error("Did not sucessfully tweet! Quitting!")
        sys.exit("Did not sucessfully tweet! Quitting!")

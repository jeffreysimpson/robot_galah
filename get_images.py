import logging
import logging.config
import shutil
from pathlib import Path
from urllib.parse import quote

import requests
from astropy import units as u
from mocpy import MOC
from PIL import Image, ImageDraw, ImageFont
import sys


def within_footprint(survey_url, the_star):
    """Checks if the star is within the footprint of a given survey."""
    survey_moc = MOC.from_fits(f"{survey_url}/Moc.fits")
    return survey_moc.contains(the_star['ra'] * u.degree,
                               the_star['dec'] * u.degree)[0]


def download_image(survey_url, the_star, logger, base_image):
    """Downloads the HiPS image.

    This research made use of hips2fits, (https://alasky.u-strasbg.fr/hips-image-services/hips2fits) a service provided by CDS."""
    width = 1000
    height = 1000
    fov = 0.25
    url = 'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips={}&width={}&height={}&fov={}&projection=TAN&coordsys=icrs&ra={}&dec={}&format=jpg&stretch=power'.format(
        quote(survey_url), width, height, fov, the_star['ra'], the_star['dec'])
    logger.debug("Trying %s", url)
    response = requests.get(url, stream=True)

    if response.status_code < 400:
        logger.debug("HTTP response: %s", response.status_code)
        with open(base_image, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
            logger.info("Saved the image to %s", base_image)
        del response
        return 0
    else:
        logger.error("BAD HTTP response: %s", response.status_code)
        del response
        return 1


def get_hips_image(the_star, secrets_dict):
    """Main function to get a sky image for the given star."""
    cwd = Path(__file__).parent
    tweet_content_dir = Path.joinpath(cwd, "tweet_content")
    config_file = Path.joinpath(cwd, 'logging.conf')
    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger('get_images')

    gaia_dr3_id = the_star['dr3_source_id']

    ohips = [['Pan-STARRS', 'http://alasky.u-strasbg.fr/Pan-STARRS/DR1/color-z-zg-g'],
             ['DECaLS',  'http://alasky.u-strasbg.fr/DECaLS/DR5/color'],
             ['DSS2',  "http://alasky.u-strasbg.fr/DSS/DSSColor"]]

    base_image = Path.joinpath(tweet_content_dir, "sky_image.jpg")

    for survey, survey_url in ohips:
        logger.info("Trying %s", survey)
        if within_footprint(survey_url, the_star):
            logger.info("Target is within footprint")
            res = download_image(survey_url, the_star, logger, base_image)
            if res == 0:
                break

    logger.info("Adding the overlay")
    # Necessary to force to a string here for the ImageFont bit.
    font = ImageFont.truetype(str(Path.joinpath(Path(secrets_dict["font_dir"]),
                                                "Roboto-Bold.ttf")),
                              40)
    try:
        img_sky = Image.open(base_image)
    except FileNotFoundError as e:
        logger.error(e)
        return 1
    draw = ImageDraw.Draw(img_sky, "RGBA")
    draw.line([((500 - 80), 500),
               ((500 - 20), 500)], fill='white', width=5)
    draw.line([(500, (500 + 80)),
               (500, (500 + 20))], fill='white', width=5)
    draw.line([(815, (1000 - 70)),
               (815 + 1000 / 15 * 2, (1000 - 70))], fill='white', width=5)
    draw.text((30, 10), f"Gaia eDR3 {gaia_dr3_id}", (255, 255, 255), font=font)
    draw.text((30, (1000 - 60)),
              f"{survey}", (255, 255, 255), font=font)
    draw.text((800, (1000 - 60)), "2 arcmin", (255, 255, 255), font=font)
    overlayed_image = Path.joinpath(tweet_content_dir, "sky_image_overlay.jpg")
    img_sky.save(overlayed_image)
    logger.info("Saved overlayed image to %s", overlayed_image)
    return survey

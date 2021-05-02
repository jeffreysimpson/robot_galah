import logging
import logging.config
import shutil
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote

import requests
from astropy import units as u
from mocpy import MOC
from PIL import Image, ImageDraw, ImageFont


def within_footprint(survey_url, the_star, logger):
    """Checks if the star is within the footprint of a given survey."""

    # PanSTARRS-1 gets a little hairy below -29.5 degrees but still returns images.
    # There are also places of no images (see Gaia eDR3 5463018973958284928)
    # but the MOC thinks there are images, but actually you get gibberish.
    if ("Pan-STARRS" in survey_url) and the_star['dec'] < 29.5:
        return False
    try:
        moc_url = f"{survey_url}/Moc.fits"
        survey_moc = MOC.from_fits(moc_url)
        return survey_moc.contains(the_star['ra'] * u.degree,
                                   the_star['dec'] * u.degree)[0]
    except HTTPError as e:
        logger.error(e)
        logger.error("Did not get the MOC file from %s. Quitting.", moc_url)
        sys.exit("Did not get the MOC file. Quitting.")


def download_image(survey_url, the_star, logger, base_image):
    """Downloads the HiPS image.

    This research made use of hips2fits,
    (https://alasky.u-strasbg.fr/hips-image-services/hips2fits)
    a service provided by CDS."""
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
    else:
        logger.error("BAD HTTP response: %s", response.status_code)
        logger.error("Did not get the sky image. Quitting.")
        sys.exit("Did not get the sky image. Quitting.")


def get_hips_image(the_star, secrets_dict):
    """Main function to get a sky image for the given star."""
    cwd = Path(__file__).parent
    tweet_content_dir = Path.joinpath(cwd, "tweet_content")
    config_file = Path.joinpath(cwd, 'logging.conf')
    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger('get_images')

    gaia_dr3_id = the_star['dr3_source_id']

    ohips = [['PanSTARRS-1', 'http://alasky.u-strasbg.fr/Pan-STARRS/DR1/color-z-zg-g'],
             ['DECaLS',  'http://alasky.u-strasbg.fr/DECaLS/DR5/color'],
             ['DSS2',  "http://alasky.u-strasbg.fr/DSS/DSSColor"]
             ]

    base_image = Path.joinpath(tweet_content_dir, "sky_image.jpg")

    for survey, survey_url in ohips:
        logger.info("Trying %s", survey)
        if within_footprint(survey_url, the_star, logger):

            logger.info("Target is within footprint of %s", survey)
            download_image(survey_url, the_star, logger, base_image)
            if base_image.is_file():
                break
        else:
            logger.info("Target is *not* within footprint of %s", survey)

    # Necessary to force to a string here for the ImageFont bit.
    font = ImageFont.truetype(str(Path.joinpath(Path(secrets_dict["font_dir"]),
                                                "Roboto-Bold.ttf")),
                              40)
    try:
        img_sky = Image.open(base_image)
    except FileNotFoundError as e:
        logger.error(e)
        logger.error("Could not load the sky image. Quitting.")
        sys.exit("Could not load the sky image. Quitting.")
    logger.info("Adding the overlay")
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

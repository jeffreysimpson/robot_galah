import logging
import logging.config
from pathlib import Path
from urllib.error import HTTPError, URLError

from astropy.coordinates import SkyCoord
from hips import WCSGeometry, make_sky_image
from PIL import Image, ImageDraw, ImageFont


def get_hips_image(the_star):

    cwd = Path.cwd()
    tweet_content_dir = Path.joinpath(cwd, "tweet_content")
    config_file = Path.joinpath(cwd, 'logging.conf')
    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger('get_images')

    gaia_dr3_id = the_star['dr3_source_id']

    geometry = WCSGeometry.create(
        skydir=SkyCoord(the_star['RA'], the_star['Dec'], unit='deg'),
        width=1000, height=1000, fov="15 arcmin", projection='AIT',
    )
    logger.info("Getting the images")
    for hips_survey in ['CDS/P/PanSTARRS/DR1/color-z-zg-g',
                        'NOAO/P/DES/DR1/LIneA-color',
                        'CDS/P/DSS2/color',
                        # 'CDS/P/Skymapper-color-IRG'
                        ]:
        logger.info("Trying %s", hips_survey)
        try:
            result = make_sky_image(geometry, hips_survey, 'jpg')
        except HTTPError:
            logger.info("No useful images from %s", hips_survey)
            continue
        except URLError as e:
            logger.error(e)
            return 1
        logger.info("Succesfully downloaded the sky image")
        base_image = Path.joinpath(tweet_content_dir, "sky_image.jpg")
        result.write_image(base_image)
        logger.info("Saved image to %s", base_image)
        break

    logger.info("Adding the overlay")
    font = ImageFont.truetype(
        "/Users/jeffreysimpson/Library/Fonts/Roboto-Bold.ttf", 40)
    img_sky = Image.open(base_image)
    draw = ImageDraw.Draw(img_sky, "RGBA")
    draw.line([((500 - 80), 500),
               ((500 - 20), 500)], fill='white', width=5)
    draw.line([(500, (500 + 80)),
               (500, (500 + 20))], fill='white', width=5)
    draw.line([(815, (1000 - 70)),
               (815 + 1000 / 15 * 2, (1000 - 70))], fill='white', width=5)
    draw.text((30, 10), f"Gaia eDR3 {gaia_dr3_id}", (255, 255, 255), font=font)
    draw.text((30, (1000 - 60)),
              f"{hips_survey.split('/')[2]}", (255, 255, 255), font=font)
    draw.text((800, (1000 - 60)), "2 arcmin", (255, 255, 255), font=font)
    overlayed_image = Path.joinpath(tweet_content_dir, "sky_image_overlay.jpg")
    img_sky.save(overlayed_image)
    logger.info("Saved overlayed image to %s", overlayed_image)
    return hips_survey

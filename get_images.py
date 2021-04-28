from urllib.error import HTTPError, URLError

from astropy.coordinates import SkyCoord
from hips import WCSGeometry, make_sky_image
from PIL import Image, ImageDraw, ImageFont
import logging
import logging.config


def get_hips_image(the_star):

    logging.config.fileConfig('logging.conf')
    # create logger
    logger = logging.getLogger('get_images')

    star_id = the_star['star_id']

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
        logger.info(f"Trying {hips_survey}")
        try:
            result = make_sky_image(geometry, hips_survey, 'jpg')
        except HTTPError:
            logger.info(f"Doesn't exist? :(")
            continue
        except URLError as e:
            logger.error(e)
            return 1
        logger.info(f"Succesfully downloaded the sky image")
        base_image = f"tweet_content/sky_image.jpg"
        result.write_image(base_image)
        logger.info(f"Saved image to {base_image}")
        break

    logger.info(f"Adding the overlay")
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
    draw.text((30, 10), f"{star_id}", (255, 255, 255), font=font)
    draw.text((30, (1000 - 60)),
              f"{hips_survey.split('/')[2]}", (255, 255, 255), font=font)
    draw.text((800, (1000 - 60)), "2 arcmin", (255, 255, 255), font=font)
    overlayed_image = f"tweet_content/sky_image_overlay.jpg"
    img_sky.save(overlayed_image)
    logger.info(f"Saved overlayed image to {overlayed_image}")
    return hips_survey

import logging
import logging.config
import shutil
import sys
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont


def download_image(survey_url, star_ra, star_dec, logger, base_image):
    """Downloads the HiPS image.

    This research made use of hips2fits,
    (https://alasky.u-strasbg.fr/hips-image-services/hips2fits)
    a service provided by CDS."""
    response = requests.get(
        url="http://alasky.u-strasbg.fr/hips-image-services/hips2fits",
        params={
            "hips": survey_url,
            "width": 1000,
            "height": 1000,
            "fov": 0.25,
            "projection": "TAN",
            "coordsys": "icrs",
            "ra": star_ra,
            "dec": star_dec,
            "format": "jpg",
            "stretch": "linear",
        },
        stream=True,
    )
    logger.debug("Tried %s", response.url)
    if response.status_code < 400:
        logger.debug("HTTP response: %s", response.status_code)
        with open(base_image, "wb") as out_file:
            shutil.copyfileobj(response.raw, out_file)
            logger.info("Saved the image to %s", base_image)
        del response
    else:
        logger.error("BAD HTTP response: %s", response.status_code)
        logger.error("%s", response.json()["title"])
        logger.error("Did not get the sky image. Quitting.")
        sys.exit("Did not get the sky image. Quitting.")


def get_best_survey(avail_hips, wanted_surveys, star_dec):
    """This ranks the avaiable HIPS in order of preference."""
    rankings = dict(zip(wanted_surveys, range(len(wanted_surveys))))
    # The PanSTARRS MOC is wrong and you get blank images for stars south of -29.5.
    # So make the PanSTARRS ranking really low for those stars.
    if star_dec < -29.5:
        rankings["CDS/P/PanSTARRS/DR1/color-z-zg-g"] = 999
    best_survey_id = wanted_surveys[
        min([rankings[avail_hip["ID"]] for avail_hip in avail_hips])
    ]
    return list(filter(lambda x: x["ID"] == best_survey_id, avail_hips))[0]


def add_overlay(
    base_image, secrets_dict, logger, tweet_content_dir, BEST_NAME, survey_name
):
    # Necessary to force to a string here for the ImageFont bit.
    font = ImageFont.truetype(
        str(Path.joinpath(Path(secrets_dict["font_dir"]), "Roboto-Bold.ttf")), 40
    )
    try:
        img_sky = Image.open(base_image)
    except FileNotFoundError as e:
        logger.error(e)
        logger.error("Could not load the sky image. Quitting.")
        sys.exit("Could not load the sky image. Quitting.")
    logger.info("Adding the overlay")
    draw = ImageDraw.Draw(img_sky, "RGBA")
    draw.line([((500 - 80), 500), ((500 - 20), 500)], fill="white", width=5)
    draw.line([(500, (500 + 80)), (500, (500 + 20))], fill="white", width=5)
    draw.line(
        [(815, (1000 - 70)), (815 + 1000 / 15 * 2, (1000 - 70))], fill="white", width=5
    )
    draw.text((30, 10), f"{BEST_NAME}", (255, 255, 255), font=font)
    draw.text((30, (1000 - 60)), f"{survey_name}", (255, 255, 255), font=font)
    draw.text((800, (1000 - 60)), "2 arcmin", (255, 255, 255), font=font)
    overlayed_image = Path.joinpath(tweet_content_dir, "sky_image_overlay.jpg")
    img_sky.save(overlayed_image)
    logger.info("Saved overlayed image to %s", overlayed_image)


def get_hips_image(star_ra, star_dec, BEST_NAME, secrets_dict):
    """Main function to get a sky image for the given star."""
    cwd = Path(__file__).parent
    tweet_content_dir = Path.joinpath(cwd, "tweet_content")
    config_file = Path.joinpath(cwd, "logging.conf")
    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger("get_images")

    base_image = Path.joinpath(tweet_content_dir, "sky_image.jpg")

    wanted_surveys = [
        "CDS/P/DECaLS/DR5/color",
        "cds/P/DES-DR1/ColorIRG",
        "CDS/P/PanSTARRS/DR1/color-z-zg-g",
        "CDS/P/SDSS9/color-alt",
        "CDS/P/DSS2/color",
    ]

    logger.info("Getting the list of useful HIPS")
    response = requests.get(
        url="http://alasky.unistra.fr/MocServer/query",
        params={
            "fmt": "json",
            "RA": star_ra,
            "DEC": star_dec,
            "SR": 0.25,
            "intersect": "enclosed",
            #                                 "dataproduct_subtype":"color",
            "fields": ",".join(["ID", "hips_service_url", "obs_title"]),
            "creator_did": ",".join([f"*{i}*" for i in wanted_surveys]),
        },
    )
    if response.status_code < 400:
        logger.debug("HTTP response: %s", response.status_code)
        avail_hips = response.json()
        for possible_survey in avail_hips:
            logger.debug("Possible HIPS options: %s", possible_survey["ID"])
        best_survey = get_best_survey(avail_hips, wanted_surveys, star_dec)
        logger.info("The best ranking survey is: %s", best_survey["ID"])
        download_image(
            best_survey["hips_service_url"], star_ra, star_dec, logger, base_image
        )
        del response
    else:
        logger.error("BAD HTTP response: %s", response.status_code)
        logger.error("%s", response.json()["title"])
        logger.error("Did not get list of HIPS. Quitting.")
        sys.exit("Did not get list of HIPS. Quitting.")

    image_source = " ".join(best_survey["ID"].split("/")[2:])
    add_overlay(
        base_image, secrets_dict, logger, tweet_content_dir, BEST_NAME, image_source
    )

    return image_source

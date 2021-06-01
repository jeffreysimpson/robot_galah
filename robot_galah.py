"""Bot for GALAH."""

import argparse
import json
import logging
import logging.config
import sys
import warnings
from datetime import datetime
from pathlib import Path
from random import choice
from urllib.parse import quote

import numpy as np
from astropy.io import fits
from astroquery.exceptions import TableParseError
from astroquery.simbad import Simbad

from do_the_tweeting import tweet
from get_images import get_hips_image
from plot_spectra import plot_spectra
from plot_stellar_params import plot_stellar_params
from astroquery.simbad import Simbad
import astropy.coordinates as coord
import astropy.units as u

greek_alphabet = {
    'alpha': 'α', 'alf': 'α',
    'beta': 'β', 'bet': 'β',
    'gamma': 'γ', 'gam': 'γ',
    'delta': 'δ', 'del': 'δ',
    'epsilon': 'ε', 'eps': 'ε',
    'zeta': 'ζ', 'zet': 'ζ',
    'eta': 'η',
    'theta': 'θ',
    'iota': 'ι',
    'kappa': 'κ', 'kap': 'κ',
    'lamda': 'λ',
    'mu': 'μ', 'mu.': 'μ',
    'nu': 'ν', 'nu.': 'ν',
    'xi': 'ξ', 'ksi': 'ξ',
    'omicron': 'ο',
    'pi': 'π',
    'rho': 'ρ',
    'sigma': 'σ',
    'tau': 'τ',
    'upsilon': 'υ',
    'phi': 'φ',
    'chi': 'χ',
    'psi': 'ψ',
    'omega': 'ω'}

constellation_names = {
    "And": "Andromedae",
    "Ant": "Antliae",
    "Aps": "Apodis",
    "Aqr": "Aquarii",
    "Aql": "Aquilae",
    "Ara": "Arae",
    "Ari": "Arietis",
    "Aur": "Aurigae",
    "Boo": "Boötis",
    "Cae": "Caeli",
    "Cam": "Camelopardalis",
    "Cnc": "Cancri",
    "CVn": "Canum Venaticorum",
    "CMa": "Canis Majoris",
    "CMi": "Canis Minoris",
    "Cap": "Capricorni",
    "Car": "Carinae",
    "Cas": "Cassiopeiae",
    "Cen": "Centauri",
    "Cep": "Cephei",
    "Cet": "Ceti",
    "Cha": "Chamaeleontis",
    "Cir": "Circini",
    "Col": "Columbae",
    "Com": "Comae Berenices",
    "CrA": "Coronae Australis",
    "CrB": "Coronae Borealis",
    "Crv": "Corvi",
    "Crt": "Crateris",
    "Cru": "Crucis",
    "Cyg": "Cygni",
    "Del": "Delphini",
    "Dor": "Doradus",
    "Dra": "Draconis",
    "Equ": "Equulei",
    "Eri": "Eridani",
    "For": "Fornacis",
    "Gem": "Geminorum",
    "Gru": "Gruis",
    "Her": "Herculis",
    "Hor": "Horologii",
    "Hya": "Hydrae",
    "Hyi": "Hydri",
    "Ind": "Indi",
    "Lac": "Lacertae",
    "Leo": "Leonis",
    "LMi": "Leonis Minoris",
    "Lep": "Leporis",
    "Lib": "Librae",
    "Lup": "Lupi",
    "Lyn": "Lyncis",
    "Lyr": "Lyrae",
    "Men": "Mensae",
    "Mic": "Microscopii",
    "Mon": "Monocerotis",
    "Mus": "Muscae",
    "Nor": "Normae",
    "Oct": "Octantis",
    "Oph": "Ophiuchi",
    "Ori": "Orionis",
    "Pav": "Pavonis",
    "Peg": "Pegasi",
    "Per": "Persei",
    "Phe": "Phoenicis",
    "Pic": "Pictoris",
    "Psc": "Piscium",
    "PsA": "Piscis Austrini",
    "Pup": "Puppis",
    "Pyx": "Pyxidis",
    "Ret": "Reticuli",
    "Sge": "Sagittae",
    "Sgr": "Sagittarii",
    "Sco": "Scorpii",
    "Scl": "Sculptoris",
    "Sct": "Scuti",
    "Ser": "Serpentis",
    "Sex": "Sextantis",
    "Tau": "Tauri",
    "Tel": "Telescopii",
    "Tri": "Trianguli",
    "TrA": "Trianguli Australis",
    "Tuc": "Tucanae",
    "UMa": "Ursae Majoris",
    "UMi": "Ursae Minoris",
    "Vel": "Velorum",
    "Vir": "Virginis",
    "Vol": "Volantis",
    "Vul": "Vulpeculae"}

superscript_map = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
    "7": "⁷", "8": "⁸", "9": "⁹"}


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


def simbad_sky_search(ra, dec):
    return Simbad.query_region(coord.SkyCoord(ra, dec,
                                              unit=(u.deg, u.deg), frame='icrs'),
                               radius='0d0m2s')


def in_simbad(the_star, logger):
    with warnings.catch_warnings():
        warnings.filterwarnings('error')
        try:
            logger.info(
                f"Searching SIMBAD for Gaia DR2 {the_star['dr2_source_id']}")
            result_table = Simbad.query_object(
                f"Gaia DR2 {the_star['dr2_source_id']}")
        except TableParseError:
            logger.info(
                f"No SIMBAD match for Gaia DR2 {the_star['dr2_source_id']}")
            try:
                logger.info(
                    "Doing a sky search around %f, %f", the_star['ra_dr2'], the_star['dec_dr2'])
                result_table = simbad_sky_search(
                    the_star['ra_dr2'], the_star['dec_dr2'])
            except TableParseError:
                logger.info(
                    f"No results for a sky search around {the_star['ra_dr2']:0.5f}, {the_star['dec_dr2']:0.5f}")
                return None
        logger.info(f"Found a match in SIMBAD: {result_table['MAIN_ID'][0]}")
        return result_table['MAIN_ID'][0]


def get_best_name(simbad_main_id,  constellation_name, logger):
    all_possible_names = Simbad.query_objectids(simbad_main_id)
    # Does this star have a common name?
    NAME_values = [" ".join(i[0].split()[1:])
                   for i in all_possible_names if i[0].startswith("NAME")]
    COMMON_NAME = None
    logger.info("Are there any NAME values?")
    if len(NAME_values) > 0:
        logger.info("All NAME values:")
        for i in NAME_values:
            logger.info(i)
        COMMON_NAME = NAME_values[0]

    # Are there any with a * ?
    asterisk_values = sorted([" ".join(i[0].split()[1:])
                             for i in all_possible_names if i[0].startswith("* ")], reverse=True)
    logger.info("Are there any * values?")
    if len(asterisk_values) > 0:
        logger.info("All asterisk_values values:")
        for i in asterisk_values:
            logger.info(i)
        best = asterisk_values[0].split()
        if best[0] in greek_alphabet:
            best[0] = greek_alphabet[best[0]]

        # There are a few stars with Greek letter and a superscript number
        if len(best[0]) > 3:
            best[0] = [best[0][:3], best[0][3:]]
            best[0][0] = greek_alphabet[best[0][0]]
            best[0][1] = superscript_map[best[0][1].replace('0', "")]
            best[0] = "".join(best[0])

        best[1] = constellation_names[best[1]]
        STAR_NAME = " ".join(best)
        if COMMON_NAME is not None:
            return f"{COMMON_NAME} ({STAR_NAME})"
        if COMMON_NAME is None:
            return f"{STAR_NAME}"

    logger.info("Are there any V* values?")
    v_asterisk_values = [" ".join(i[0].split()[1:])
                         for i in all_possible_names if i[0].startswith("V* ")]
    if len(v_asterisk_values) > 0:
        logger.info("All V* values", v_asterisk_values)
        best = v_asterisk_values[0].split()
        best[1] = constellation_names[best[1]]
        STAR_NAME = " ".join(best)
        return f"{STAR_NAME}"

    for possible_start in ["HD ", "HIP ",
                           "CD-",
                           "BD-", "BD+",
                           "CPD-",
                           "TYC "
                           ]:
        logger.info(f"Are there any {possible_start} values?")
        id_values = [i[0]
                     for i in all_possible_names if i[0].startswith(possible_start)]
        if len(id_values) > 0:
            logger.info("All %s values:", possible_start)
            for i in id_values:
                logger.info(i)
            STAR_NAME = " ".join(id_values[0].split())
            return f"{STAR_NAME}"

    logger.debug([i[0] for i in all_possible_names])

def distance_str(the_star):
    distance = the_star['distance_bstep'] * 1000
    e_distance = the_star['e_distance_bstep'] * 1000
    error_size = 10 ** (len(str(abs(int(e_distance))))-1)
    rounded_distance = int(np.round(distance / error_size) * error_size)
    if rounded_distance < 1000:
        return f"{rounded_distance} pc"
    if rounded_distance > 1000:
        return f"{rounded_distance/1000:0.1f} kpc"

def mass_str(the_star):
    return f"{the_star['m_act_bstep']:0.1f} solar masses"

def age_str(the_star):
    if the_star['age_bstep'] >= 1:
        return f"{the_star['age_bstep']:0.1f} Gyr"
    if the_star['age_bstep'] < 1:
        return f"{the_star['age_bstep']*1000:0.0f} Myr"

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
    if tweet_content_dir.exists():
        logger.debug(
            "Deleting the old files in %s if they exist", tweet_content_dir.as_posix())
        for f in tweet_content_dir.iterdir():
            if f.is_file:
                logger.debug("Deleting %s", f.name)
                f.unlink()
    else:
        logger.debug(
            "Creating directory at %s", tweet_content_dir.as_posix())
        tweet_content_dir.mkdir(parents=True, exist_ok=True)

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
                  "other": "during a special programme", }

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
    logger.debug("RA = %f, Dec = %f", the_star['ra'], the_star['dec'])

    d = datetime.strptime(str(the_star['sobject_id'])[:6], "%y%m%d").date()
    obs_date_str = d.strftime('%-d %b %Y')
    survey_name = the_star['survey_name']

    # There are about 300 otherwise good stars that lack BSTEP data
    if not np.isnan(the_star['age_bstep']):
        HAS_BSTEP = True
        distance = distance_str(the_star)
        mass = mass_str(the_star)
        age = age_str(the_star)
    else:
        logger.warning("No BSTEP values for this star!")
        HAS_BSTEP = False

    constellation_name = coord.get_constellation(coord.SkyCoord(the_star['ra_dr2'],
                                                                the_star['dec_dr2'],
                                                                unit=(u.deg, u.deg), frame='icrs'))

    simbad_main_id = in_simbad(the_star, logger)
    if simbad_main_id is None:
        BEST_NAME = f"Gaia eDR3 {the_star['dr3_source_id']}"
        cds_url = f"http://cdsportal.u-strasbg.fr/?target={quote(' '.join([str(the_star['ra']), str(the_star['dec'])]))}"
    else:
        cds_url = f"http://cdsportal.u-strasbg.fr/?target={quote(simbad_main_id)}"
        BEST_NAME = get_best_name(simbad_main_id, constellation_name, logger)
        if BEST_NAME is None:
            logger.warning("No best name!")
            BEST_NAME = f"Gaia eDR3 {the_star['dr3_source_id']}"

    logger.info("Creating the tweet text:")
    tweet_list = []
    tweet_list.append(f"{choice(BIRD_WORDS).upper()}!")
    tweet_list.append(f"We observed {BEST_NAME} in the constellation of {constellation_name} on {obs_date_str} {survey_str[survey_name]}.")
    if HAS_BSTEP:
        tweet_list.append(f"It is {distance} from the Sun, aged {age}, and is {mass}.")
    tweet_list.append(f"Find out more about this star {cds_url}")
    tweet_text = "\n\n".join(tweet_list)
    for l in tweet_list:
        logger.info(l)

    plot_stellar_params(galah_dr3, the_star, BEST_NAME, basest_idx_galah)
    hips_survey = get_hips_image(the_star, BEST_NAME, secrets_dict)
    plot_spectra(the_star, BEST_NAME)
    tweet(tweet_text, hips_survey, BEST_NAME, secrets_dict, DRY_RUN)


if __name__ == "__main__":
    main()

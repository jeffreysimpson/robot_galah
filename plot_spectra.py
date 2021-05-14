
import logging
import logging.config
import sys
from pathlib import Path

import astropy.units as u
import galah_plotting
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.constants import c
from astropy.io import fits
from matplotlib import rcParams
from matplotlib.offsetbox import AnchoredText
from pyvo.dal.exceptions import DALFormatError, DALServiceError
from pyvo.dal.ssa import SSAService

# URL of the SSA service
URL = "https://datacentral.org.au/vo/ssa/query"
service = SSAService(URL)


def plot_spectra(the_star):

    rcParams['font.family'] = "sans-serif"
    rcParams['font.sans-serif'] = ["Roboto"]
    rcParams['figure.facecolor'] = 'white'
    plt.style.use("dark_background")

    cwd = Path(__file__).parent
    tweet_content_dir = Path.joinpath(cwd, "tweet_content")
    config_file = Path.joinpath(cwd, 'logging.conf')
    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger('plot_spectra')

    custom = {}
    custom['TARGETNAME'] = the_star['sobject_id']
    # only retrieve the normalised spectra
    custom['DPSUBTYPE'] = 'normalised'
    custom['COLLECTION'] = 'galah_dr3'
    logger.info("Grabbing the spectra files")
    try:
        results = service.search(**custom)
    except(DALServiceError, DALFormatError) as e:
        logger.error(e)
        logger.error("Did not get the list of spectra. Quitting.")
        sys.exit("Did not get the list of spectra. Quitting.")
    indiv_results = []
    indiv_results.append(results.votable.get_first_table().to_table(
        use_names_over_ids=True).to_pandas())

    bands_names = ["B", "V", "R", "I"]

    band_dict = {"B": {"color": "C4", "ticks": np.arange(4730, 4900, 75), "name": "blue"},
                 "V": {"color": "C0", "ticks": np.arange(5680, 5900, 75), "name": "green"},
                 "R": {"color": "C3", "ticks": np.arange(6500, 6900, 75), "name": "red"},
                 "I": {"color": "C2", "ticks": np.arange(7610, 7900, 75), "name": "infrared"}}

    df = pd.concat(indiv_results, ignore_index=True)

    plot_list_base = [[i] for i in ['B', 'V', 'R', 'I']]

    rv_correction = (
        c / ((the_star['rv_galah'] * u.km / u.s) + c)).decompose().value

    fig, axes, redo_axes_list, *_ = galah_plotting.initialize_plots(
        figsize=(3, 4),
        #     things_to_plot=plot_list_base,
        specific_layout=plot_list_base,
    )

    if np.isnan(the_star['rv_galah']):
        rv_correction = 1.
        logger.debug("rv_galah is a nan")
    else:
        rv_correction = (
            c / ((the_star['rv_galah'] * u.km / u.s) + c)).decompose().value
        logger.debug("Applying an RV correction of %s", rv_correction)

    for *_, spec_row in df.iterrows():
        url = spec_row['access_url'] + "&RESPONSEFORMAT=fits"
        logger.info("Opening %s", url)
        with fits.open(url) as spec:
            wl = np.linspace(float(spec[0].header['WMIN']),
                             float(spec[0].header['WMAX']),
                             len(spec[0].data))
            axes[spec_row['band_name']].plot(wl * rv_correction,
                                             spec[0].data,
                                             c=band_dict[spec_row['band_name']
                                                         ]['color'],
                                             lw=0.5)

        redo_axes_list[spec_row['band_name']].update(
            {"xticks": band_dict[spec_row['band_name']]['ticks'],
             "yticks": [],
             "xlim": np.percentile(wl, [0, 100]) + [-3, 3],
             "ylim": [0, 1.2]
             })

    redo_axes_list["I"].update(
        {"xlabel": 'Wavelength (angstroms)',
         })

    axes['B'].set_title(
        f"Normalized HERMES spectrum of\nGaia eDR3 {the_star['dr3_source_id']}")

    for missing_band in [band for band in bands_names if band not in df['band_name'].to_list()]:
        redo_axes_list[missing_band].update(
            {"xticks": [],
             "yticks": [],
             "ylim": [0, 1.2]
             })
        logger.info("Missing the spectra for the %s camera", missing_band)
        anchored_text = AnchoredText(f"This star does not have an {band_dict[missing_band]['name']} camera spectrum.",
                                     loc='center',
                                     frameon=False, pad=0,
                                     prop=dict(color=band_dict[missing_band]['color']))
        axes[missing_band].add_artist(anchored_text)

    galah_plotting.redo_plot_lims(axes, redo_axes_list)
    spec_file = Path.joinpath(tweet_content_dir, "spectra.png")
    logger.info("Saving spectrum to %s", spec_file)
    fig.savefig(spec_file, bbox_inches='tight',
                dpi=500, transparent=False)
    return 0

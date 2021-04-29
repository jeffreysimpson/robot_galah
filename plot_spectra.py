
import logging
import logging.config
from pathlib import Path

import astropy.units as u
import galah_plotting
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.constants import c
from astropy.io import fits
from matplotlib import rcParams
from pyvo.dal.exceptions import DALFormatError
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
    except DALFormatError as e:
        logger.error(e)
        return 1
    indiv_results = []
    indiv_results.append(results.votable.get_first_table().to_table(
        use_names_over_ids=True).to_pandas())

    df = pd.concat(indiv_results, ignore_index=True)

    plot_list_base = [[i] for i in ['B', 'V', 'R', 'I']]

    colour_dict = {"B": "C4",
                   "V": "C0",
                   "R": "C3",
                   "I": "C2"
                   }

    ticks_dict = {"B": np.arange(4730, 4900, 75),
                  "V": np.arange(5680, 5900, 75),
                  "R": np.arange(6500, 6900, 75),
                  "I": np.arange(7610, 7900, 75),
                  }

    rv_correction = (
        c / ((the_star['rv_galah'] * u.km / u.s) + c)).decompose().value

    fig, axes, redo_axes_list, *_ = galah_plotting.initialize_plots(
        figsize=(3, 4),
        #     things_to_plot=plot_list_base,
        specific_layout=plot_list_base,
    )

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
                                             c=colour_dict[spec_row['band_name']],
                                             lw=0.5)

        redo_axes_list[spec_row['band_name']].update(
            {"xticks": ticks_dict[spec_row['band_name']],
             "yticks": [],
             "xlim": np.percentile(wl, [0, 100]) * [0.999, 1.0001],
             "ylim": [0, 1.2]
             })

    redo_axes_list["I"].update(
        {"xlabel": 'Wavelength (angstroms)',
         })

    axes['B'].set_title(
        f"Normalized HERMES spectrum of\nGaia eDR3 {the_star['dr3_source_id']}")
    galah_plotting.redo_plot_lims(axes, redo_axes_list)
    spec_file = Path.joinpath(tweet_content_dir, "spectra.png")
    logger.info("Saving spectrum to %s", spec_file)
    fig.savefig(spec_file, bbox_inches='tight',
                dpi=500, transparent=False)
    return 0

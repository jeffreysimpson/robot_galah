import logging
import logging.config
# from os.path import dirname, join
from pathlib import Path

import galah_plotting
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rcParams  # font_manager,
from matplotlib.colors import LogNorm


def plot_stellar_params(galah_dr3, the_star, basest_idx_galah):

    rcParams['font.family'] = "sans-serif"
    rcParams['font.sans-serif'] = ["Roboto"]
    rcParams['figure.facecolor'] = 'white'
    plt.style.use("dark_background")

    cwd = Path.cwd()
    tweet_content_dir = Path.joinpath(cwd, "tweet_content")
    config_file = Path.joinpath(cwd, 'logging.conf')
    logging.config.fileConfig(config_file)
    # create logger
    logger = logging.getLogger('plot_stellar_params')

    plot_list_bases = [[
        ['teff', 'logg'],
        ['fe_h', 'alpha_fe']
    ], [
        ['L_Z', 'Energy'],
        ['V_UVW', 'U_UVW_W_UVW']
    ]]

    for plot_list_base in plot_list_bases:
        logger.info(f"Creating the {plot_list_base} plot")
        fig, axes, redo_axes_list, *_ = galah_plotting.initialize_plots(
            figsize=(2.*1.15, 4*1.15),
            things_to_plot=plot_list_base,
            nrows=2, ncols=1
        )

        the_star_highlight = [
            {"idx": galah_dr3['sobject_id'] == the_star['sobject_id'],
             "kwargs": dict(s=50, marker='*', lw=0.4, alpha=1.,
                            c='C3', zorder=100,
                            label='GES stars'), "errors": False},
        ]

        for stars_to_highlight in [[], the_star_highlight]:
            galah_plotting.plot_base_all(
                plot_list_base,
                stars_to_highlight,
                basest_idx_galah,
                axes,
                table=galah_dr3,
                SCATTER_DENSITY=True,
                scatter_density_kwarg=dict(cmap='viridis',
                                           zorder=0,
                                           alpha=1.0,
                                           dpi=75,
                                           norm=LogNorm(vmin=1,
                                                        vmax=2000)))
        if plot_list_base[0][0] == "teff":
            redo_axes_list['teff__logg'].update(
                {"xticks": np.arange(4500, 9000, 1000),
                 "yticks": np.arange(0, 6, 1),
                 "xlim": [8000, 4000],
                 # "xlabel": 'Effective temperature (K)',
                 # "ylabel": 'Surface gravity',
                 })

            redo_axes_list['fe_h__alpha_fe'].update(
                {"xticks": np.arange(-3, 2, 1),
                 "yticks": np.arange(-1, 3, 1),
                 # "xlabel": '[Fe/H]',
                 # "ylabel": '[α/Fe]',
                 "xlim": [-2.7, 0.7],
                 "ylim": [-1.2, 1.5]
                 })
            axes['teff__logg'].set_title(
                f"Stellar parameters of\nGaia eDR3 {the_star['dr3_source_id']}")
        if plot_list_base[0][0] == "L_Z":
            redo_axes_list['L_Z__Energy'].update(
                {"xticks": np.arange(-4, 5, 2),
                 "yticks": np.arange(-4, 1, 1),
                 "xlim": [-2.5, 4.1],
                 "ylim": [-3., -0.8],
                 })
            redo_axes_list['V_UVW__U_UVW_W_UVW'].update(
                {"xticks": np.arange(-400, 200, 200),
                 "yticks": np.arange(0, 500, 200),
                 "xlim": [-500, 100],
                 "ylim": [0, 500],
                 })
            axes['L_Z__Energy'].set_title(
                f"Orbital properties of\nGaia eDR3 {the_star['dr3_source_id']}")
        galah_plotting.redo_plot_lims(axes, redo_axes_list)
        # plt.show()
        save_file_loc = Path.joinpath(
            tweet_content_dir, f"stellar_params_{plot_list_base[0][0]}.png")
        try:
            fig.savefig(save_file_loc, bbox_inches='tight',
                        dpi=500, transparent=False)
        except TypeError as e:
            logger.error(e)
            return 1
        # fig.close()
        logger.info(f"Saved plot to {save_file_loc}")
        plt.close(fig)

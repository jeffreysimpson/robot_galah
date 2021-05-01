Robot GALAH
-------------

This is a small Python script to tweet information about a random star from the [GALAH survey](https://www.galah-survey.org).

Here's what I have used to run it:
* Python 3.9+
* [Tweepy](http://www.tweepy.org/)
* [pyvo](https://pyvo.readthedocs.io/en/latest/)
* [astropy](https://www.astropy.org)
* [mocpy](https://cds-astro.github.io/mocpy/)
* matplotlib, numpy, pandas, Pillow, requests
* galah_plotting: this is a personal package I have for some convenience functions to plot GALAH data.

Data
-------------
The star is randomly chosen from [GALAH DR3](https://docs.datacentral.org.au/galah/dr3/overview/). As recommended by the GALAH team, all the stars have `flag_sp = 0`, `flag_fe_h = 0`, and `snr_c3_iraf > 30`. Ages, distances, and masses are from the [`galah_dr3.vac_ages` value-added catalogue](https://docs.datacentral.org.au/galah/dr3/value-added-catalogues/).

Images
-------------
This research makes use of [`hips2fits`](http://alasky.u-strasbg.fr/hips-image-services/hips2fits) a service provided by CDS. The overlay on each image is created in `PIL`.

Spectra
-------------
The spectra are retrieved using the [Simple Spectral Access](https://www.ivoa.net/documents/cover/SSA-20071220.html) protocol from [Data Central](https://datacentral.org.au).

The specific code is inspired/modified from [this example](https://docs.datacentral.org.au/help-center/virtual-observatory-examples/ssa-galah-dr3/).



License
-------

Robot GALAH is provided under the MIT license. See `LICENSE.TXT` for more information.

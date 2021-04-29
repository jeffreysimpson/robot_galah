Robot GALAH
-------------

This is a small Python script to tweet information about a random star from the [GALAH survey](https://www.galah-survey.org).

Here's what I have used to run it:
* Python 3.9+
* [Tweepy](http://www.tweepy.org/)
* [pyvo](https://pyvo.readthedocs.io/en/latest/)
* [astropy](https://www.astropy.org)
* [hips](https://hips.readthedocs.io/en/latest/)
* matplotlib, numpy, pandas, Pillow
* galah_plotting: this is a personal package I have for some convenience functions to plot GALAH data.

Getting the spectra
-------------
The spectra are retrieved using the [Simple Spectral Access](https://www.ivoa.net/documents/cover/SSA-20071220.html) protocol from [Data Central](https://datacentral.org.au).

The specific code is modified from [this example](https://docs.datacentral.org.au/help-center/virtual-observatory-examples/ssa-galah-dr3/).



License
-------

Robot GALAH is provided under the MIT license. See `LICENSE.TXT` for more information.

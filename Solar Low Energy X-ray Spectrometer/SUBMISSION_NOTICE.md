SUBMISSION NOTICE

This project uses an external dataset for labeling:
- GOES X-ray event lists from NOAA NCEI/NGDC (public-domain U.S. Government data). See https://www.ngdc.noaa.gov/stp/satellite/goes/.

I confirm:
- The GOES event list is used only for labeling and evaluation; the operational nowcast detector uses SoLEXS-only inputs.
- GOES data used is public-domain; relevant citation and URL are included in `DATASETS.md` and `README.md`.
- No restricted or proprietary external datasets are included in the submission package.

If the hackathon organizers require removal of external data, the code supports running the SoLEXS-only pipeline without GOES labels (see `scripts/plot_solexs.py` and the detector script). Please instruct if you want the final submission to exclude any external files.

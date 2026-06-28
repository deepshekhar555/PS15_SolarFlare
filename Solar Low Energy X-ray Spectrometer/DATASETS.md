DATASETS used in this repository

### 🌐 Project Hosted Datasets
Due to the file size limitations of large raw telemetry data (~900MB), the raw instrument files and pre-processed ML-ready tables are hosted externally:
* **Hugging Face Hub Repository**: `https://huggingface.co/datasets/YOUR_USERNAME/aditya-l1-solar-flare` *(Placeholder - update after uploading)*
* **Google Drive Public Link (Full ZIP)**: `https://drive.google.com/open?id=YOUR_FILE_ID` *(Placeholder - update after uploading)*
* For detailed instructions on how to upload or download these packages, refer to the root [SHARE_DATASET.md](../SHARE_DATASET.md) guide.

---

1) SoLEXS combined lightcurves (local)
- Description: Combined SoLEXS FITS lightcurve files (Aditya-L1 instrument).
- Local path used in this repo: `data/` (original inputs) and `output/solexs_combined.csv` (combined CSV)
- License/permissions: provided with project; verify you have rights to redistribute if packaging submission.
- Notes: This is the primary operational input for the SoLEXS-only nowcasting pipeline.

2) GOES X-ray event list (NOAA NCEI/NGDC)
- Description: GOES X-ray event lists (flare start/peak/end times and NOAA class labels) used as labeling ground-truth for evaluation and catalog creation.
- URL / source page: https://www.ngdc.noaa.gov/stp/satellite/goes/
- Local file used: `data/goes_xray_2026.txt`
- License/permissions: NOAA NCEI/NGDC data is U.S. Government public domain (generally reusable). Confirm specific dataset use with event organizers if needed.
- Download date (used in this repo): 2026-06-19
- Citation: NOAA NCEI/NGDC GOES X-ray event lists (https://www.ngdc.noaa.gov/stp/satellite/goes/)

Guidance
- Always include `DATASETS.md` within any submission ZIP and include the URLs + download dates in your submission form. If you add other external datasets, append them here with URL, license and download date.

Additional recommended public solar datasets (optional)

3) SDO/AIA imagery (sample)
- Description: Full-disk EUV images from the Solar Dynamics Observatory Atmospheric Imaging Assembly (AIA).
- URL / source page: https://sdo.gsfc.nasa.gov/ (JSOC / Helioviewer APIs can provide cutouts)
- Usage note: imagery is large; include only small sample cutouts (via Helioviewer) for demonstrations. Confirm contest rules for large external imagery.

4) RHESSI event list (hard X-rays)
- Description: RHESSI flare catalogs provide timing and HXR info useful for impulsive-phase validation.
- URL / source page: https://hesperia.gsfc.nasa.gov/rhessi3/ or RHESSI flare list mirrors
- Local support: `scripts/fetch_additional_datasets.py` includes a validated HESSI URL for `rhessi_flare_list.txt`.
- Usage note: event lists are small text files suitable for labeling and cross-checking.

5) Fermi/GBM solar flare catalogs
- Description: Fermi/GBM can provide solar flare trigger and event timing as an additional HXR catalog.
- URL / source page: public mirror URLs for Fermi/GBM solar catalogs are not always stable; use local files if manually obtained.
- Usage note: `scripts/label_flares.py` supports a local `data/fermi_gbm_flare_list.txt` file for optional catalog fusion.

6) SOHO/LASCO — CDAW CME catalog
- Description: CME listings (time, speed, width) from CDAW at NASA/GSFC.
- URL: https://cdaw.gsfc.nasa.gov/CME_list/
- Usage note: useful to correlate flares with CMEs; text tables are small.

6) NOAA/SWPC products
- Description: Additional event reports and alerts from NOAA Space Weather Prediction Center.
- URL: https://www.swpc.noaa.gov/ or https://www.ngdc.noaa.gov/stp/space-weather/
- Usage note: complements GOES event lists.

7) Ground-based H-alpha flare catalogs (e.g., Kanzelhöhe)
- Description: Optical flare records from ground observatories.
- Usage note: optional cross-validation; check licensing.

8) Helioviewer / SunPy APIs
- Description: APIs and tools to retrieve imagery cutouts, time series snippets, and quicklook plots.
- URL: https://helioviewer.org/ and https://sunpy.org/
- Usage note: recommended for small sample downloads only.

Notes on adding datasets
- Do not download full image archives unless you intend to host them or include them in the submission and have explicit permission — instead fetch small samples or event-lists.
- For each added dataset, append an entry with URL, local filename, download date, and license/permission text.

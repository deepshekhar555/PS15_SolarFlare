PS15_SolarFlare — SoLEXS Nowcasting (Aditya-L1)

Summary
- Repository for SoLEXS-only nowcasting pipeline developed for a Hack2Skill / ISRO submission (BAH 2026 PS#15).

Data sources
- SoLEXS combined lightcurves: local (pre-provided) files under `data/` and combined into `output/solexs_combined.csv`.
- GOES X-ray event list (for labeling): NOAA NCEI/NGDC GOES event lists (public domain). Example source page: https://www.ngdc.noaa.gov/stp/satellite/goes/ . We used `data/goes_xray_2026.txt` as the event-list file and included attribution in `scripts/label_flares.py` outputs.

Notes on competition rules
- NOAA GOES data is public-domain U.S. government data and is generally permissible to use in hackathons; however, always confirm the specific hackathon's dataset/external-data rules.
- Hack2Skill resources: https://hack2skill.com and the Hack2Skill YouTube channel: https://www.youtube.com/@hack2skill

Repro steps
1. Fetch or place GOES event list: `data/goes_xray_2026.txt` (optional: run `py scripts/fetch_goes.py 2026` to attempt download).
2. Combine SoLEXS FITS (already done): `output/solexs_combined.csv`.
3. Label SoLEXS with external X-ray event catalogs: `py scripts/label_flares.py` (produces `output/labeled_solexs.csv` and `output/matched_flares.csv`).
   - Optional local files: `data/rhessi_flare_list.txt` and `data/fermi_gbm_flare_list.txt`.
4. Generate plots: `py scripts/plot_solexs.py` (produces `output/solexs_plot_YYYYMMDD.png` and `output/solexs_plot_zoom.png`).

Attribution
- GOES X-ray event lists: NOAA NCEI/NGDC — https://www.ngdc.noaa.gov/stp/satellite/goes/

If you want, I can also generate a short 1–2 page PDF summary for submission and include these citations in the PDF. Please confirm and I'll produce it.

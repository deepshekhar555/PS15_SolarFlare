# 📊 Sharing and Hosting the Aditya-L1 Solar Flare Dataset

This guide provides step-by-step instructions on how to host and share the project's datasets (both raw telemetry and processed ML-ready features) using **Hugging Face Hub**, **Google Drive**, or **Kaggle Datasets**.

Due to the size of the raw telemetry files (~900MB total, mostly HEL1OS data), these files are excluded from Git version control via `.gitignore`. By hosting them on a dedicated dataset repository, you enable seamless collaboration and reproduction.

---

## 🚀 Option 1: Hugging Face Hub (Recommended)

Hugging Face is the gold standard for hosting AI and machine learning datasets. It is completely free, supports large files, provides built-in versioning, and has native integration with Python.

We have provided an automated script [`scripts/upload_to_hf.py`](file:///d:/PS15_SolarFlare/scripts/upload_to_hf.py) to upload your data to Hugging Face in one command.

### Step 1: Install Dependency
Make sure you have the `huggingface_hub` package installed:
```bash
pip install huggingface_hub
```

### Step 2: Get a WRITE Token
1. Create a free account or log in at [Hugging Face](https://huggingface.co/).
2. Go to **Settings > Access Tokens** (or [click here](https://huggingface.co/settings/tokens)).
3. Click **Create new token**, set the type to **Write**, and give it a name (e.g., `aditya-l1-solar-flare`).
4. Copy the token.

### Step 3: Run the Upload Script
Run the script from your terminal:
```bash
python scripts/upload_to_hf.py
```
The script will interactively guide you:
- Select whether you want to upload the **Processed Dataset (~50MB)**, **Raw Dataset (~900MB)**, **Workspace ZIP (~890MB)**, or **All**.
- Paste your Hugging Face WRITE token.
- Enter your desired repository name (defaults to `username/aditya-l1-solar-flare`).
- Choose whether to make the repository public or private.

Once the upload finishes, your dataset will be live at:
`https://huggingface.co/datasets/YOUR_USERNAME/aditya-l1-solar-flare`

### Step 4: How Others Can Load Your Shared Data
Once uploaded, anyone can load the processed files directly from the web using Python:
```python
import pandas as pd

# Load the combined nowcast event catalog
catalog_url = "https://huggingface.co/datasets/YOUR_USERNAME/aditya-l1-solar-flare/raw/main/processed_output/solexs_hel1os_combined_catalog.csv"
df_catalog = pd.read_csv(catalog_url)
print(df_catalog.head())
```

---

## 📂 Option 2: Google Drive (Colab Integration)

If you are sharing files with team members who are running the project inside Google Colab (using [`PS15_SolarFlare_Colab.ipynb`](file:///d:/PS15_SolarFlare/PS15_SolarFlare_Colab.ipynb)), hosting the files on Google Drive is highly convenient.

### Step 1: Package the Project
Ensure your local project zip package is generated and up-to-date:
```bash
python zip_workspace.py
```
This generates `PS15_SolarFlare.zip` in your root directory, excluding temporary files and virtual environments, but including the `data/` and `output/` folders.

### Step 2: Upload to Google Drive
1. Open your browser and go to [Google Drive](https://drive.google.com/).
2. Upload the `PS15_SolarFlare.zip` file to your drive.
3. To make it accessible to others or your Colab script without manual logins:
   - Right-click the uploaded ZIP file, select **Share > Share**.
   - Under **General access**, change "Restricted" to **"Anyone with the link"** (set role to **Viewer**).
   - Click **Copy link**.

### Step 3: Accessing via Google Colab
For team members running the Colab notebook:
1. Open [`PS15_SolarFlare_Colab.ipynb`](file:///d:/PS15_SolarFlare/PS15_SolarFlare_Colab.ipynb) in Google Colab.
2. Under **Step 1: Mount Google Drive**, mount your Google Drive.
3. If using a shared link instead of a personal drive, you can use `gdown` to download it directly into Colab:
   ```python
   !pip install --upgrade gdown
   !gdown --id YOUR_GOOGLE_DRIVE_FILE_ID -O /content/PS15_SolarFlare.zip
   ```
   *(To get your file ID, extract the long alphanumeric string from the copied Google Drive link).*

---

## 🏆 Option 3: Kaggle Datasets

Kaggle is perfect for public portfolio presentation and hackathon showcase. It has a beautiful interface that displays schema descriptions and column statistics automatically.

### Step 1: Package the Dataset
Organize the folders you want to upload. It is recommended to create a separate folder on your computer containing:
```
aditya-l1-solar-flare-dataset/
├── processed_output/
│   ├── solexs_hel1os_combined_catalog.csv
│   └── forecast_results_rf.csv
└── raw_data/
    ├── goes_xray_2026.txt
    └── [raw files if size permits]
```

### Step 2: Upload via Web UI
1. Go to [Kaggle Datasets](https://www.kaggle.com/datasets) and log in.
2. Click the **"+ New Dataset"** button in the top right.
3. Enter a title (e.g., `Aditya-L1 Solar Flare Dataset`).
4. Drag and drop your dataset folder or ZIP file.
5. Click **Create** to compile and publish the dataset.

---

## 📝 Updating Project Documentation

After you upload your datasets, make sure to update the following files in your repository to point to your new hosted URLs:

1. **`README.md`**: Update the **"📊 Datasets & Data Sharing"** section with the direct links.
2. **`Solar Low Energy X-ray Spectrometer/DATASETS.md`**: Update the local path descriptions to include the hosted URLs.

This ensures that anyone cloning your repository knows exactly where to fetch the large telemetry files to run your pipelines.

import json
import os

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# ☀️ Solar Flare Nowcast & Forecast Pipeline (Google Colab Edition)\n",
    "\n",
    "Welcome to the Google Colab environment for the **PS15 Solar Flare Project**! This notebook is designed to help you run the entire data processing and machine learning training pipeline in the cloud using Google Colab's powerful environment.\n",
    "\n",
    "### 📋 How to Get Started:\n",
    "1. **Upload the ZIP file**: Upload `PS15_SolarFlare.zip` (located in your local project folder) to your **Google Drive** (preferably in the root directory or in the `Colab Notebooks` folder).\n",
    "2. **Upload this Notebook**: Open [Google Colab](https://colab.research.google.com/), select the **Upload** tab, and upload this `PS15_SolarFlare_Colab.ipynb` file.\n",
    "3. **Run the cells sequentially**: Run each cell below by clicking the **Play** button or pressing `Shift + Enter`."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## 📂 Step 1: Mount Google Drive\n",
    "We mount your Google Drive to access the compressed project ZIP file."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "from google.colab import drive\n",
    "drive.mount('/content/drive')"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## 📦 Step 2: Extract Project Files\n",
    "We locate `PS15_SolarFlare.zip` on your Google Drive and extract it to the local Colab temporary storage (`/content/PS15_SolarFlare`). This provides fast file I/O operations during data processing and model training."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import zipfile\n",
    "\n",
    "# Path to the zip file on Google Drive (we check the root and Colab Notebooks folder)\n",
    "zip_path = '/content/drive/MyDrive/PS15_SolarFlare.zip'\n",
    "extract_path = '/content/PS15_SolarFlare'\n",
    "\n",
    "if not os.path.exists(zip_path):\n",
    "    possible_paths = [\n",
    "        '/content/drive/MyDrive/PS15_SolarFlare.zip',\n",
    "        '/content/drive/MyDrive/Colab Notebooks/PS15_SolarFlare.zip'\n",
    "    ]\n",
    "    for p in possible_paths:\n",
    "        if os.path.exists(p):\n",
    "            zip_path = p\n",
    "            break\n",
    "\n",
    "if os.path.exists(zip_path):\n",
    "    print(f\"✅ Found zip file at: {zip_path}\")\n",
    "    print(\"🔄 Extracting files... (This may take 1-2 minutes due to large datasets)\")\n",
    "    with zipfile.ZipFile(zip_path, 'r') as zip_ref:\n",
    "        zip_ref.extractall(extract_path)\n",
    "    print(\"🎉 Extraction complete! Project is ready at '/content/PS15_SolarFlare'\")\n",
    "else:\n",
    "    print(\"❌ ERROR: PS15_SolarFlare.zip not found on Google Drive!\")\n",
    "    print(\"Please upload the ZIP file to your Google Drive root directory and try again.\")\n",
    "    print(\"Alternatively, you can upload the zip file directly to Colab's left sidebar and update 'zip_path' accordingly.\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## 🛠️ Step 3: Install Dependencies\n",
    "We change our working directory to the extracted project folder and install all the required Python libraries using `requirements.txt`."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "%cd /content/PS15_SolarFlare\n",
    "!pip install -r requirements.txt"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## 🔄 Step 4: Run Data Preprocessing Pipeline\n",
    "We execute the data processing scripts to combine SoLEXS raw data zip files, detect nowcast events, and label them using the external GOES and RHESSI catalogs."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "print(\"=== 1. Combining SoLEXS Raw ZIPs ===\")\n",
    "!python \"Solar Low Energy X-ray Spectrometer/scripts/combine_solexs.py\"\n",
    "\n",
    "print(\"\\n=== 2. Generating SoLEXS Nowcast Events ===\")\n",
    "!python \"Solar Low Energy X-ray Spectrometer/scripts/generate_solexs_nowcast.py\"\n",
    "\n",
    "print(\"\\n=== 3. Labeling Flares with External Catalogs ===\")\n",
    "!python \"Solar Low Energy X-ray Spectrometer/scripts/label_flares.py\""
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## 🤖 Step 5: Train Machine Learning Models\n",
    "We train the leakage-free forecasting models: the Single-Instrument model (using scikit-learn) and the Dual-Instrument Fusion model (which integrates both high and low-energy instruments)."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "print(\"=== 1. Training Single-Instrument Forecaster ===\")\n",
    "!python scripts/train_forecast_sklearn.py\n",
    "\n",
    "print(\"\\n=== 2. Training Dual-Instrument Fusion Forecaster ===\")\n",
    "!python scripts/train_forecast_dual_fusion.py"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "--- \n",
    "## 📊 Step 6: Launch Interactive Streamlit Dashboard\n",
    "You can run the Streamlit dashboard directly from Google Colab! We use `localtunnel` to create a public secure tunnel to access the dashboard running inside this container.\n",
    "\n",
    "### ℹ️ Instructions:\n",
    "1. **Copy your Public IP**: The cell below will print a public IP address (e.g., `35.230.x.x`). **Copy this IP address** as you will need it as the password.\n",
    "2. **Click the Link**: A link ending in `.localtunnel.me` or `ipv4.icanhazip.com` will appear. Click the localtunnel link.\n",
    "3. **Enter Password**: Paste the public IP address into the \"Tunnel Password\" input box on the webpage and click **Submit**.\n",
    "4. Enjoy your interactive dashboard!"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 1. Get the public IP address (needed as the password for localtunnel)\n",
    "print(\"========================================================\")\n",
    "print(\"🔴 COPY THIS IP ADDRESS (Tunnel Password):\")\n",
    "!curl -s ipv4.icanhazip.com\n",
    "print(\"========================================================\\n\")\n",
    "\n",
    "# 2. Install localtunnel\n",
    "print(\"Installing localtunnel...\")\n",
    "!npm install -g localtunnel &>/dev/null\n",
    "print(\"localtunnel installed successfully!\\n\")\n",
    "\n",
    "# 3. Run Streamlit in the background\n",
    "import subprocess\n",
    "print(\"Starting Streamlit server in the background...\")\n",
    "subprocess.Popen([\"streamlit\", \"run\", \"dashboard.py\", \"--server.port\", \"8501\", \"--server.address\", \"0.0.0.0\"], \n",
    "                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n",
    "\n",
    "# 4. Start localtunnel to expose port 8501\n",
    "print(\"Creating public secure tunnel...\")\n",
    "print(\"Click the link below when it appears, and paste the IP address from above into the form:\")\n",
    "!npx localtunnel --port 8501"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}

with open("PS15_SolarFlare_Colab.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)
print("Created PS15_SolarFlare_Colab.ipynb successfully!")

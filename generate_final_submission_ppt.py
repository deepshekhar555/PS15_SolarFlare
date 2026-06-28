import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def generate_ppt():
    src_path = r"d:\PS15_SolarFlare\BAH_PPT (1).pptx"
    dst_path = r"d:\PS15_SolarFlare\AdityaL1_SolarFlare_BAH_2026.pptx"
    
    if not os.path.exists(src_path):
        print(f"Error: Source file {src_path} not found.")
        sys.exit(1)
        
    print("Loading presentation template...")
    prs = Presentation(src_path)
    
    # Define colors
    BLUE_DARK = RGBColor(10, 25, 47)
    GREEN = RGBColor(0, 150, 100)
    TEXT_DARK = RGBColor(40, 40, 40)
    WHITE = RGBColor(255, 255, 255)
    
    # Helpers
    def set_shape_text(shape, text, size_pt=14, bold=False, color=TEXT_DARK, font_name='Arial'):
        shape.text = ""
        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.name = font_name
        p.font.size = Pt(size_pt)
        p.font.bold = bold
        p.font.color.rgb = color
        return p

    def replace_picture_shape(slide, shape, img_path, custom_coords=None):
        if not os.path.exists(img_path):
            print(f"Warning: Image {img_path} not found, skipping replacement.")
            return
        left = custom_coords[0] if custom_coords else shape.left
        top = custom_coords[1] if custom_coords else shape.top
        width = custom_coords[2] if custom_coords else shape.width
        height = custom_coords[3] if custom_coords else shape.height
        # Remove old shape
        slide.shapes._spTree.remove(shape._element)
        # Add new picture
        slide.shapes.add_picture(img_path, left, top, width, height)
        print(f"Replaced picture with image {os.path.basename(img_path)}")

    # =========================================================================
    # SLIDE 1: Title Slide
    # =========================================================================
    print("Modifying Slide 1: Title...")
    slide1 = prs.slides[0]
    for shape in slide1.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text
            if "Team Name" in text:
                set_shape_text(shape, "Team Name : SuryaDrishti", 24, True, WHITE)
            elif "Team Leader Name" in text:
                set_shape_text(shape, "Team Leader Name : Deep Shekhar Halder", 18, True, WHITE)
            elif "Problem Statement" in text:
                set_shape_text(shape, "Problem Statement : PS15 - Real-Time Solar Flare Nowcasting and Forecasting Using ISRO Aditya-L1 X-Ray Telemetry", 16, False, RGBColor(0, 210, 140))

    # =========================================================================
    # SLIDE 2: Team Members
    # =========================================================================
    print("Modifying Slide 2: Team Members...")
    slide2 = prs.slides[1]
    for shape in slide2.shapes:
        if shape.has_table:
            table = shape.table
            
            # Leader (Cell 0, 0)
            cell_leader = table.cell(0, 0)
            cell_leader.text = ""
            tf = cell_leader.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = "Team Leader & Tech Lead\nName: Deep Shekhar Halder\nEmail: deephalder209@gmail.com\nCollege: Adamas University, Kolkata"
            p.font.size = Pt(13)
            p.font.name = 'Arial'
            p.font.color.rgb = TEXT_DARK
            
            # Member 1 (Cell 0, 1)
            cell_m1 = table.cell(0, 1)
            cell_m1.text = ""
            tf_m1 = cell_m1.text_frame
            tf_m1.word_wrap = True
            p_m1 = tf_m1.paragraphs[0]
            p_m1.text = "Team Member-1 (Data & Preprocessing)\nName: Rituraj Saha\nEmail: saharituraj805@gmail.com\nCollege: Adamas University, Kolkata"
            p_m1.font.size = Pt(13)
            p_m1.font.name = 'Arial'
            p_m1.font.color.rgb = TEXT_DARK
            
            # Member 2 (Cell 1, 0)
            cell_m2 = table.cell(1, 0)
            cell_m2.text = ""
            tf_m2 = cell_m2.text_frame
            tf_m2.word_wrap = True
            p_m2 = tf_m2.paragraphs[0]
            p_m2.text = "Team Member-2 (ML Modeling & Validation)\nName: Mahalaxmi Macha\nEmail: mahalaxmimacha14@gmail.com\nCollege: Adamas University, Kolkata"
            p_m2.font.size = Pt(13)
            p_m2.font.name = 'Arial'
            p_m2.font.color.rgb = TEXT_DARK
            
            # Member 3 (Cell 1, 1)
            cell_m3 = table.cell(1, 1)
            cell_m3.text = ""
            tf_m3 = cell_m3.text_frame
            tf_m3.word_wrap = True
            p_m3 = tf_m3.paragraphs[0]
            p_m3.text = "Team Member-3 (Dashboard & Benchmarking)\nName: Ashfaque Ahamed Khan\nEmail: ashfaqueahamedkhan591@gmail.com\nCollege: Adamas University, Kolkata"
            p_m3.font.size = Pt(13)
            p_m3.font.name = 'Arial'
            p_m3.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 3: Brief about the Idea
    # =========================================================================
    print("Modifying Slide 3: Brief about the Idea...")
    slide3 = prs.slides[2]
    
    idea_text = (
        "Project SuryaDrishti is an autonomous, space-weather alert dashboard and prediction pipeline built directly for "
        "ISRO Aditya-L1 ground operations. It fuses multi-wavelength X-ray telemetry on a 1-second cadence to nowcast and forecast "
        "solar flares and their terrestrial space weather impacts.\n\n"
        "• Multi-Instrument Fusion: Synchronizes SoLEXS (Soft X-rays, 1-22 keV) and HEL1OS (Hard X-rays, 10-150 keV) on a 1-second cadence.\n"
        "• Causal Nowcasting Core: Employs a zero-lookahead rolling statistical threshold engine to identify flare onset, peak, and decay phases without temporal leakage.\n"
        "• Pre-Flare Precursor Alarm: Detects inflection in the SoLEXS counts derivative, providing a 10-30 minute early warning before flare peak.\n"
        "• Differential Emission Measure (DEM): Resolves the coronal temperature distribution (T_max, emission measure EM) in real-time using Tikhonov regularization.\n"
        "• Solar Energetic Particles (SEP) & Parker Spiral: Models solar proton flux arrival times using Tylka-Dietrich regression and Parker Spiral magnetic connection probability."
    )
    
    for shape in slide3.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text
            if "A Multi-Modal" in text or "Diffusion-Powered" in text:
                set_shape_text(shape, idea_text, 11.5, False, TEXT_DARK)
                # Move the body text box lower to avoid overlap with the title and orange box
                shape.top = Inches(2.8)
                shape.height = Inches(4.3)
            elif "Project K.A.L.A.M." in text or "Atmospheric Metamodels" in text:
                # Use BLUE_DARK instead of WHITE to make it visible on the light background
                set_shape_text(shape, "Project SuryaDrishti - Autonomous Space Weather Alert System\n(Real-Time Solar Flare Nowcasting & Forecasting Dashboard)", 14, True, BLUE_DARK)
                shape.top = Inches(1.5)
                shape.height = Inches(1.0)
            elif "Brief about the Idea" in text:
                shape.top = Inches(0.5)

    # =========================================================================
    # SLIDE 4: Opportunity & USP
    # =========================================================================
    print("Modifying Slide 4: Opportunity & USP...")
    slide4 = prs.slides[3]
    
    opportunity_text = (
        "How different is it from other existing ideas?\n"
        "• Traditional methods rely on post-facto centered smoothing windows (incorporating future data points), making them undeployable in real-time. We implement a strictly causal rolling baseline.\n"
        "• Prior works treat SXR and HXR as separate catalogs; we perform raw, 1-second cadence multi-instrument telemetry fusion to compute physical properties in real time.\n\n"
        "How will it be able to solve the problem?\n"
        "• Aditya-L1 provides high-cadence X-ray measurements. By combining SoLEXS and HEL1OS telemetry, we capture the full thermodynamic evolution of solar flares.\n"
        "• Predicts impending flares 30 minutes in advance using RandomForest models trained on physics-informed precursors (QPPs, hardness ratio).\n"
        "• Protects satellites and power grids from sudden radiation surges."
    )
    
    usp_text = (
        "USP of the proposed solution\n"
        "1. Strictly Causal Nowcasting: Zero-lookahead baseline achieves 93.2% recall against NOAA GOES.\n"
        "2. Real-Time Telemetry Fusion: Aligns SXR and HXR on a 1-second cadence to model the Neupert Effect.\n"
        "3. Physics-Informed Precursors: Reconstructs coronal plasma heating (slow rise) and non-thermal acceleration (QPPs and hardness ratio).\n"
        "4. Sub-Threshold Discovery: Detects 136 microflares absent from official NOAA catalogs."
    )
    
    for shape in slide4.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text
            if "How different is it" in text or "Traditional methods" in text:
                set_shape_text(shape, opportunity_text, 11, False, TEXT_DARK)
            elif "USP of the proposed solution" in text or "Hybrid Physics-AI Core" in text:
                set_shape_text(shape, usp_text, 11, False, TEXT_DARK)
                # Shift USP text box down slightly to align nicely inside the black box
                shape.top = Inches(2.05)
                shape.left = Inches(6.1)
                shape.width = Inches(6.5)

    # =========================================================================
    # SLIDE 5: Features Offered
    # =========================================================================
    print("Modifying Slide 5: Features...")
    slide5 = prs.slides[4]
    
    features_text = (
        "Features offered by the Solution:\n"
        "• Multi-Instrument Ingestion & Harmonization: Automates calibration and alignment of raw FITS files from SoLEXS and HEL1OS.\n"
        "• Real-Time Causal Nowcasting: Detects solar flare onset, peak, and decay phases using dynamic statistical thresholds.\n"
        "• Physics-Informed Predictive Modeling: Forecasts impending flares 30 minutes in advance using rolling physics-backed precursors.\n"
        "• Live Operator Dashboard & Alerts: Displays live counts, risk probabilities, and color-coded hazard alerts (Green, Yellow, Red)."
    )
    
    for shape in slide5.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text
            if "Smart Multi-Band" in text:
                set_shape_text(shape, features_text, 11, False, TEXT_DARK)
            elif "Features offered by the Solution:" in text:
                # Clear the redundant title shape to prevent overlap
                shape.text = ""
            elif "Raw ( 5 band images )" in text or "Raw (" in text:
                set_shape_text(shape, "SoLEXS Soft X-Ray (1-22 keV)", 10, True, TEXT_DARK)
            elif "Preprocessed Images" in text:
                set_shape_text(shape, "SUIT NUV Wavelength (200-400 nm)", 10, True, TEXT_DARK)
            elif "*POC of our idea" in text:
                set_shape_text(shape, "*Proof-of-concept developed on real Aditya-L1 telemetry (259,071 overlap timestamps, 16 flares)", 9, True, TEXT_DARK)
    
    # Coordinate-based replacement for Slide 5 illustrations (threshold 2.0")
    for shape in list(slide5.shapes):
        if shape.shape_type == 13: # PICTURE
            if shape.width < Inches(10.0):
                if shape.top < Inches(2.0):
                    replace_picture_shape(slide5, shape, r"C:\Users\Welcome\.gemini\antigravity-ide\brain\9e2c343a-18e1-4f1e-a5de-6e3c5f218cd7\sun_orange_1782612178444.png")
                else:
                    replace_picture_shape(slide5, shape, r"C:\Users\Welcome\.gemini\antigravity-ide\brain\9e2c343a-18e1-4f1e-a5de-6e3c5f218cd7\sun_purple_1782612290904.png")

    # =========================================================================
    # SLIDE 6: Process Flow
    # =========================================================================
    print("Modifying Slide 6: Process Flow...")
    slide6 = prs.slides[5]
    
    for shape in slide6.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text.strip()
            if text == "Satellite":
                set_shape_text(shape, "Aditya-L1 Spacecraft", 9, True, TEXT_DARK)
            elif text == "Database":
                set_shape_text(shape, "ISSDC Data Portal", 9, True, TEXT_DARK)
            elif text == "Preprocessing Pipeline":
                set_shape_text(shape, "Telemetry Ingestion & Calibration", 9, True, TEXT_DARK)
            elif "Model" in text and "Architecture" in text:
                set_shape_text(shape, "Causal Nowcasting & RandomForest Core", 9, True, TEXT_DARK)
            elif text == "Predicted Frames":
                set_shape_text(shape, "30-Min Forecast (Holt-Winters)", 9, True, TEXT_DARK)
            elif text == "Input Frames":
                set_shape_text(shape, "Pre-Flare Precursors (QPPs, HR)", 9, True, TEXT_DARK)
            elif text == "Self Supervised Learning":
                set_shape_text(shape, "Tikhonov DEM Inversion", 9, True, TEXT_DARK)
            elif text == "Dashboard":
                set_shape_text(shape, "Operator Dashboard (Streamlit/HTML5)", 9, True, TEXT_DARK)
            elif text == "(POC)":
                set_shape_text(shape, "(Real-time Web HUD)", 9, True, TEXT_DARK)
            elif "* We will add a self supervised" in text:
                set_shape_text(shape, "* Real-time telemetry fusion of SoLEXS and HEL1OS provides multi-wavelength situational awareness for ISRO space weather operations.", 10, False, TEXT_DARK)
    
    # Replace the old cloud motion screenshot
    for shape in list(slide6.shapes):
        if shape.shape_type == 13:
            if shape.width < Inches(10.0) and shape.left < Inches(5.0):
                replace_picture_shape(slide6, shape, r"C:\Users\Welcome\.gemini\antigravity-ide\brain\9e2c343a-18e1-4f1e-a5de-6e3c5f218cd7\new_realistic_sun_dashboard_1782612674526.png")

    # =========================================================================
    # SLIDE 7: Wireframes / Mockups
    # =========================================================================
    print("Modifying Slide 7: Wireframes...")
    slide7 = prs.slides[6]
    
    for shape in slide7.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text
            if "Wireframes/Mock diagrams" in text:
                set_shape_text(shape, "Operator Interface & Real-Time Visualization Mockups", 20, True, BLUE_DARK)
            elif "* We will predict" in text:
                set_shape_text(shape, "* Real-time interactive dashboard featuring 3D solar disk visualization, active region monitoring, and automated threat alerts.", 12, False, TEXT_DARK)
    
    # Delete the old cloud-motion table
    for shape in list(slide7.shapes):
        if shape.has_table:
            slide7.shapes._spTree.remove(shape._element)
            
    # Replace the wireframe picture with custom coordinates that fit exactly on the 10x5.625 slide
    for shape in list(slide7.shapes):
        if shape.shape_type == 13:
            if shape.width < Inches(10.0):
                replace_picture_shape(slide7, shape, r"C:\Users\Welcome\.gemini\antigravity-ide\brain\9e2c343a-18e1-4f1e-a5de-6e3c5f218cd7\new_realistic_sun_dashboard_1782612674526.png", 
                                      custom_coords=(Inches(0.43), Inches(1.25), Inches(9.23), Inches(3.6)))

    # =========================================================================
    # SLIDE 8: Architecture
    # =========================================================================
    print("Modifying Slide 8: Architecture...")
    slide8 = prs.slides[7]
    
    # Delete detailed shapes
    shapes_to_delete = list(slide8.shapes)[2:]
    for s in shapes_to_delete:
        slide8.shapes._spTree.remove(s._element)
        
    # Add a clean text box sized perfectly for the 10" slide
    arch_box = slide8.shapes.add_textbox(Inches(0.75), Inches(1.5), Inches(8.5), Inches(3.8))
    tf_arch = arch_box.text_frame
    tf_arch.word_wrap = True
    
    p_arch = tf_arch.paragraphs[0]
    p_arch.text = "System Architecture of Project SuryaDrishti"
    p_arch.font.name = 'Arial'
    p_arch.font.size = Pt(18)
    p_arch.font.bold = True
    p_arch.font.color.rgb = BLUE_DARK
    p_arch.space_after = Pt(10)
    
    arch_bullets = [
        "**1. Telemetry Ingestion & Calibration Layer**:\n   - Automatically fetches and parses raw FITS files from the Aditya-L1 ISSDC portal.\n   - Extracts Soft X-ray (SoLEXS) and Hard X-ray (HEL1OS) count rates.\n   - Converts MJD timestamps to a unified Unix epoch, interpolating to a synchronized 1-second cadence.",
        "**2. Physics-Informed Feature Engineering Layer**:\n   - Thermal Precursors: Computes the 10-minute rolling mean and positive slope of SoLEXS counts to capture slow-rise plasma heating.\n   - Non-Thermal Precursors: Computes the rolling standard deviation of HEL1OS counts to isolate high-frequency QPP oscillations.\n   - Neupert Effect: Calculates the Spectral Hardness Ratio (HEL1OS / SoLEXS) to model energy transfer from accelerated electrons to thermal plasma.",
        "**3. Causal Nowcasting & Machine Learning Core**:\n   - Zero-Lookahead Nowcaster: Applies sliding-window statistical thresholds to classify flare phases (onset, peak, decay) without lookahead bias.\n   - RandomForest Classifier: Trained on chronological, leakage-free splits using balanced class weights to predict flare occurrence 30 minutes in advance.",
        "**4. Space Weather Impact & Visualisation HUD**:\n   - Renders a 3D WebGL solar disk showing active regions (AR4087, AR4086, AR4085).\n   - Computes Differential Emission Measure (DEM) via Tikhonov regularization.\n   - Models CME propagation via the Drag-Based Model (DBM) and SEP proton flux via Tylka-Dietrich regression.\n   - Emits real-time visual and audio alerts (Web Audio API) for satellite protection."
    ]
    for b in arch_bullets:
        p = tf_arch.add_paragraph()
        p.text = b
        p.font.name = 'Arial'
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(4)

    # =========================================================================
    # SLIDE 9: Tech Stack & POC Prototype
    # =========================================================================
    print("Modifying Slide 9: Tech Stack & POC...")
    slide9 = prs.slides[8]
    
    tech_stack_bullets = (
        "• Modeling & Forecasting:\n"
        "  - Scikit-learn (RandomForest Classifier)\n"
        "  - SciPy (Tikhonov DEM Inversion & Holt-Winters Forecasting)\n"
        "  - Joblib (Model serialization & caching)\n\n"
        "• Data & Preprocessing:\n"
        "  - Astropy (FITS telemetry processing)\n"
        "  - NumPy & Pandas (Data merging, cleaning, alignment)\n\n"
        "• Interface & Visualization:\n"
        "  - HTML5, Vanilla CSS, JavaScript (ES6+)\n"
        "  - Chart.js (Interactive plotting of telemetry, QPP, DEM)\n"
        "  - Web Audio API (Operator alert sound engine)\n\n"
        "• Backend & Deployment:\n"
        "  - Python HTTP Server (lightweight, local deployment)\n"
        "  - Node.js (Syntax validation and testing)"
    )
    
    for shape in list(slide9.shapes):
        if shape.has_text_frame:
            text = shape.text_frame.text
            if "Modeling & Forecasting" in text:
                set_shape_text(shape, tech_stack_bullets, 11, False, TEXT_DARK)
                # Position the body text box neatly
                shape.top = Inches(2.2)
                shape.width = Inches(5.5)
                shape.height = Inches(4.5)
            elif "Tech Stack for K.A.L.A.M." in text or "Tech Stack for Project" in text:
                # Set the title textbox and increase its width to 5.5" to prevent wrapping
                set_shape_text(shape, "Tech Stack for Project SuryaDrishti", 18, True, BLUE_DARK)
                shape.width = Inches(5.5)
                shape.top = Inches(1.5)
                shape.height = Inches(0.6)
            elif "POC of Model Prototype" in text:
                set_shape_text(shape, "DEM Plasma Temperature Inversion", 10, True, TEXT_DARK)
            elif "Performance Matrices" in text:
                set_shape_text(shape, "CME & SEP Propagation Trackers", 10, True, TEXT_DARK)
            elif "Wind Direction Predictions" in text:
                # Delete the old vertical text box
                slide9.shapes._spTree.remove(shape._element)
    
    # Coordinate-based replacement for Slide 9 illustrations (threshold 1.8")
    for shape in list(slide9.shapes):
        if shape.shape_type == 13:
            if shape.width < Inches(10.0):
                if shape.top < Inches(1.8):
                    replace_picture_shape(slide9, shape, r"C:\Users\Welcome\.gemini\antigravity-ide\brain\9e2c343a-18e1-4f1e-a5de-6e3c5f218cd7\dem_diagnostics_dashboard_1782621919601.png")
                else:
                    replace_picture_shape(slide9, shape, r"C:\Users\Welcome\.gemini\antigravity-ide\brain\9e2c343a-18e1-4f1e-a5de-6e3c5f218cd7\sep_risk_tab_mockup_1782622548223.png")

    # =========================================================================
    # SLIDE 10: Estimated Cost
    # =========================================================================
    print("Modifying Slide 10: Cost...")
    slide10 = prs.slides[9]
    
    for shape in slide10.shapes:
        if shape.has_text_frame:
            text = shape.text_frame.text
            if "Estimated implementation cost" in text:
                set_shape_text(shape, "Estimated Implementation Cost :", 20, True, BLUE_DARK)
            elif "FIXED COST" in text:
                set_shape_text(shape, "FIXED COST (ONE-TIME SETUP):", 14, True, GREEN)
            elif "= ₹" in text:
                set_shape_text(shape, "= ₹4,85,000 (Estimated Cost (may vary based on final deployment and resources.))", 12, True, BLUE_DARK)
                
    # Update cost table
    for shape in slide10.shapes:
        if shape.has_table:
            table = shape.table
            
            costs_data = [
                ["Telemetry Ingestion & Fusion Pipeline", "₹50,000", "Multi-instrument (SoLEXS & HEL1OS) FITS data alignment."],
                ["Causal Nowcasting Engine", "₹50,000", "Zero-lookahead rolling statistical threshold detector."],
                ["Physics-Informed ML Forecaster", "₹1,00,000", "RandomForest model trained on precursor features."],
                ["Interactive Operator Dashboard", "₹40,000", "Streamlit web interface with real-time risk alerts."],
                ["NOAA GOES Validation System", "₹40,000", "Benchmarking engine for automated cross-validation."],
                ["Local Workstation GPU", "₹1,50,000", "Hardware for training and telemetry hosting."],
                ["Documentation & SOP Handover", "₹30,000", "Operational guidelines for space-weather centers."],
                ["Public Dashboard Deployment", "₹25,000", "Secure public hosting and remote access configuration."]
            ]
            
            for r_idx, row_data in enumerate(costs_data):
                for c_idx, val in enumerate(row_data):
                    cell = table.cell(r_idx + 1, c_idx)
                    cell.text = ""
                    p = cell.text_frame.paragraphs[0]
                    p.text = val
                    p.font.size = Pt(11)
                    p.font.name = 'Arial'
                    p.font.color.rgb = TEXT_DARK

    # =========================================================================
    # SLIDE 11: References
    # =========================================================================
    print("Modifying Slide 11: References...")
    slide11 = prs.slides[10]
    
    ref_text = (
        "Scientific References\n"
        "-----------------------------------------------------------------------\n"
        "1. Sarwade et al., 2025: In-flight calibration and performance of the Solar Low Energy X-ray Spectrometer (SoLEXS) onboard Aditya-L1. Solar Physics.\n"
        "2. Nandi et al., 2025: Hard X-ray diagnostics of solar flares: First results from HEL1OS onboard Aditya-L1. The Astrophysical Journal.\n"
        "3. Tylka & Dietrich, 2009: A new parameterization of solar energetic proton (SEP) spectra. Proceedings of the 31st International Cosmic Ray Conference.\n"
        "4. Vrsnak et al., 2013: Propagation of Interplanetary Coronal Mass Ejections: The Drag-Based Model. Solar Physics.\n"
        "5. Dere et al., 1997: CHIANTI - an atomic database for emission lines. Astronomy and Astrophysics Supplement Series.\n\n"
        "Other Resources\n"
        "-----------------------------------------------------------------------\n"
        "• ISRO ISSDC Aditya-L1 Data Portal (SoLEXS and HEL1OS level-1 telemetry logs).\n"
        "• NOAA Space Weather Prediction Center (GOES XRS solar flare event catalog).\n"
        "• COntinuous Spectral Inversion (COSI) framework for Differential Emission Measure (DEM) diagnostics."
    )
    
    for shape in slide11.shapes:
        if shape.has_text_frame and "Research Papers" in shape.text_frame.text:
            set_shape_text(shape, ref_text, 11, False, TEXT_DARK)

    # =========================================================================
    # SLIDE 12: Thank You
    # =========================================================================
    print("Modifying Slide 12: Thank You...")
    slide12 = prs.slides[11]
    
    thank_you_text = (
        "We, as a dedicated team, are excited to solve this problem and actively contribute to India's AI vision for space weather monitoring.\n\n"
        "Project SuryaDrishti provides a robust, scientifically grounded, and deployment-ready dashboard to protect India's space assets."
    )
    
    for shape in slide12.shapes:
        if shape.has_text_frame and "We, as a dedicated team" in shape.text_frame.text:
            set_shape_text(shape, thank_you_text, 14, True, BLUE_DARK)

    # Save presentation
    prs.save(dst_path)
    print(f"\nSuccess! Presentation saved at: {dst_path}")

if __name__ == "__main__":
    generate_ppt()

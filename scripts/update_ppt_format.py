import os
import sys
import copy
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE_TYPE

# Reconfigure stdout to use UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def find_shape_by_text(slide, query):
    for shape in slide.shapes:
        if shape.has_text_frame and query in shape.text_frame.text:
            return shape
    return None

def find_shape_by_name(slide, name):
    for shape in slide.shapes:
        if shape.name == name:
            return shape
    return None

def delete_shape(slide, shape):
    try:
        sp = shape.element
        sp.getparent().remove(sp)
    except Exception as e:
        print(f"Error deleting shape {shape.name}: {e}")

def copy_shape_smart(shape, dest_slide, slide_idx, shape_idx):
    # If the shape is a picture, copy the actual image binary safely using a URI-safe filename
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        try:
            # INTERCEPT PICTURE 41 on Slide 5 to inject our own dashboard screenshot
            if slide_idx == 5 and shape.name == "Picture 41":
                custom_img = "Solar Low Energy X-ray Spectrometer/output/dashboard_screenshot.png"
                if os.path.exists(custom_img):
                    new_shape = dest_slide.shapes.add_picture(custom_img, shape.left, shape.top, width=shape.width, height=shape.height)
                    return new_shape
            
            # INTERCEPT GOOGLE SHAPE;128;P3 on Slide 5 to inject our realistic Aditya-L1 image
            if slide_idx == 5 and shape.name == "Google Shape;128;p3":
                custom_img = "Solar Low Energy X-ray Spectrometer/output/aditya_l1_observing_sun.png"
                if os.path.exists(custom_img):
                    new_shape = dest_slide.shapes.add_picture(custom_img, shape.left, shape.top, width=shape.width, height=shape.height)
                    return new_shape
            
            # INTERCEPT PICTURE 2 on Slide 7 to inject our RandomForest diagram
            if slide_idx == 7 and shape.name == "Picture 2":
                custom_img = "Solar Low Energy X-ray Spectrometer/output/random_forest_architecture.png"
                if os.path.exists(custom_img):
                    new_shape = dest_slide.shapes.add_picture(custom_img, shape.left, shape.top, width=shape.width, height=shape.height)
                    return new_shape
            
            image = shape.image
            image_bytes = image.blob
            ext = f".{image.ext}" if hasattr(image, 'ext') and image.ext else '.png'
            
            # Use a clean, alphanumeric filename to avoid OPC XML parsing errors
            temp_path = f"temp_image_s{slide_idx}_sh{shape_idx}{ext}"
            with open(temp_path, "wb") as f:
                f.write(image_bytes)
            # Add picture to destination slide
            new_shape = dest_slide.shapes.add_picture(temp_path, shape.left, shape.top, width=shape.width, height=shape.height)
            os.remove(temp_path)
            return new_shape
        except Exception as e:
            print(f"Error copying picture shape {shape.name}: {e}")
            # Fallback to XML copy
            el = shape.element
            new_el = copy.deepcopy(el)
            dest_slide.shapes._spTree.append(new_el)
            return dest_slide.shapes[-1]
    else:
        # Standard XML copy for other shape types (flowchart blocks, lines, connectors, groups, tables)
        el = shape.element
        new_el = copy.deepcopy(el)
        dest_slide.shapes._spTree.append(new_el)
        return dest_slide.shapes[-1]

def copy_shapes_between_slides_smart(src_slide, dest_slide, skip_names, slide_idx):
    copied_shapes = []
    for shape_idx, shape in enumerate(src_slide.shapes):
        if shape.name in skip_names:
            continue
        new_shape = copy_shape_smart(shape, dest_slide, slide_idx, shape_idx)
        if new_shape is not None:
            copied_shapes.append(new_shape)
    return copied_shapes

def format_slide_title(shape, title_text, navy_color):
    if shape.has_text_frame:
        tf = shape.text_frame
        tf.text = title_text
        p = tf.paragraphs[0]
        p.font.name = 'Google Sans'
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = navy_color
        p.alignment = PP_ALIGN.LEFT

def create_clean_title(slide, placeholder_query, title_text, navy_color):
    # Find and delete layout-inherited placeholder text box to prevent double titles/ghosting
    s_ph = find_shape_by_text(slide, placeholder_query)
    if s_ph:
        delete_shape(slide, s_ph)
    # Create a fresh text box in the exact title slot
    title_box = slide.shapes.add_textbox(Inches(0.34), Inches(0.4), Inches(8.28), Inches(0.5))
    format_slide_title(title_box, title_text, navy_color)
    return title_box

def update_title_slide_shape(shape, prefix, value, text_color):
    if shape.has_text_frame:
        tf = shape.text_frame
        found = False
        for p in tf.paragraphs:
            for r in p.runs:
                if prefix in r.text:
                    r.text = f"{prefix} {value}"
                    r.font.color.rgb = text_color
                    r.font.name = 'Google Sans Medium'
                    r.font.size = Pt(16)
                    r.font.bold = True
                    found = True
                    break
            if found:
                break
        if not found:
            tf.text = f"{prefix} {value}"
            p = tf.paragraphs[0]
            p.font.name = 'Google Sans Medium'
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = text_color

def main():
    template_path = "[Pub] ISRO BAH 2026 _ Idea Submission Template.pptx"
    source_flowchart_path = "BAH_PPT (1).pptx"
    output_path = "AdityaL1_SolarFlare_Presentation.pptx"
    
    if not os.path.exists(template_path):
        print(f"Error: Official template presentation '{template_path}' not found!")
        sys.exit(1)
        
    if not os.path.exists(source_flowchart_path):
        print(f"Error: Source presentation '{source_flowchart_path}' not found!")
        sys.exit(1)
        
    print(f"Loading official template: {template_path}")
    prs = Presentation(template_path)
    
    print(f"Loading source flowcharts: {source_flowchart_path}")
    prs_src = Presentation(source_flowchart_path)
    
    # Colors
    NAVY = RGBColor(10, 25, 47)
    WHITE = RGBColor(255, 255, 255)
    TEXT_DARK = RGBColor(40, 40, 40)
    DARK_GRAY = RGBColor(32, 39, 41) # Original dark color on slide 1
    
    # ==========================================
    # SLIDE 1: Title Slide (Light Background)
    # ==========================================
    print("Modifying Slide 1 (Title)...")
    s1 = prs.slides[0]
    
    # Preserve original Google Sans font and dark color to keep text visible
    s_team = find_shape_by_text(s1, "Team Name :")
    if s_team:
        update_title_slide_shape(s_team, "Team Name :", "SuryaDrishti", DARK_GRAY)
            
    s_leader = find_shape_by_text(s1, "Team Leader Name :")
    if s_leader:
        update_title_slide_shape(s_leader, "Team Leader Name :", "Deep Shekhar Halder", DARK_GRAY)
            
    s_problem = find_shape_by_text(s1, "Problem Statement :")
    if s_problem:
        update_title_slide_shape(s_problem, "Problem Statement :", "PS15 - Real-Time Solar Flare Nowcasting and Forecasting Using ISRO Aditya-L1 X-Ray Telemetry", DARK_GRAY)

    # ==========================================
    # SLIDE 2: Team Members Table
    # ==========================================
    print("Modifying Slide 2 (Team Members Table)...")
    s2 = prs.slides[1]
    
    s_title2 = find_shape_by_text(s2, "Team Members")
    if s_title2:
        format_slide_title(s_title2, "Team Members", NAVY)
        
    s_table = None
    for shape in s2.shapes:
        if shape.has_table:
            s_table = shape.table
            break
            
    if s_table:
        def format_cell(cell, role, name, email):
            cell.text = ""
            tf = cell.text_frame
            tf.word_wrap = True
            
            p1 = tf.paragraphs[0]
            p1.text = role
            p1.font.name = 'Arial'
            p1.font.bold = True
            p1.font.size = Pt(12)
            p1.font.color.rgb = NAVY
            
            p2 = tf.add_paragraph()
            p2.text = f"Name: {name}"
            p2.font.name = 'Arial'
            p2.font.bold = False
            p2.font.size = Pt(11)
            p2.font.color.rgb = TEXT_DARK
            
            p3 = tf.add_paragraph()
            p3.text = f"Email: {email}"
            p3.font.name = 'Arial'
            p3.font.bold = False
            p3.font.size = Pt(10)
            p3.font.color.rgb = TEXT_DARK
            
            p4 = tf.add_paragraph()
            p4.text = "College: Adamas University, Kolkata"
            p4.font.name = 'Arial'
            p4.font.bold = False
            p4.font.size = Pt(10)
            p4.font.color.rgb = TEXT_DARK

        format_cell(s_table.cell(0, 0), "Team Leader & Tech Lead", "Deep Shekhar Halder", "deephalder209@gmail.com")
        format_cell(s_table.cell(0, 1), "Team Member-1 (Data & Preprocessing)", "Rituraj Saha", "saharituraj805@gmail.com")
        format_cell(s_table.cell(1, 0), "Team Member-2 (ML Modeling & Validation)", "Mahalaxmi Macha", "mahalaxmimacha14@gmail.com")
        format_cell(s_table.cell(1, 1), "Team Member-3 (Dashboard & Benchmarking)", "Ashfaque Ahamed Khan", "ashfaqueahamedkhan591@gmail.com")
    else:
        print("Warning: Table on Slide 2 not found!")

    # ==========================================
    # SLIDE 3: Opportunity
    # ==========================================
    print("Modifying Slide 3 (Opportunity)...")
    s3 = prs.slides[2]
    
    # Create clean title shape (deletes placeholder to avoid double title)
    create_clean_title(s3, "Opportunity should be able to explain", "Opportunity & USP", NAVY)
        
    # Place opportunity details in a new content textbox below the title
    content_box3 = s3.shapes.add_textbox(Inches(0.34), Inches(1.35), Inches(9.32), Inches(3.9))
    tf3 = content_box3.text_frame
    tf3.word_wrap = True
    tf3.text = (
        "• How different is it from other existing ideas?\n"
        "  Traditional solar flare detection methods rely on post-facto centered smoothing windows (such as Gaussian or Savitzky-Golay filters) that incorporate future data points (t + dt), making them impossible to deploy in real-time telemetry feeds. We implement a strictly causal rolling baseline to process live telemetry feeds. Furthermore, prior works treat SXR and HXR as separate catalogs; we perform raw, 1-second cadence multi-instrument telemetry fusion to compute physical properties in real time.\n\n"
        "• How will it be able to solve the problem?\n"
        "  Aditya-L1 provides high-cadence X-ray measurements. By combining SoLEXS (Soft X-rays) and HEL1OS (Hard X-rays) telemetry, we capture the full thermodynamic evolution of solar flares. Our causal nowcasting baseline dynamically identifies flare start, peak, and decay phases. Using engineered physics precursors, we train RandomForest models to forecast flare occurrence 30 minutes in advance, enabling operators to protect satellites and power grids from sudden radiation surges.\n\n"
        "• USP of the proposed solution:\n"
        "  1. Strictly Causal Nowcasting: Zero-lookahead baseline achieves 93.2% recall against NOAA GOES.\n"
        "  2. Real-Time Telemetry Fusion: Aligns SXR and HXR on a 1-second cadence to model the Neupert Effect.\n"
        "  3. Physics-Informed Precursors: Calculates coronal plasma heating (slow rise) and non-thermal acceleration (QPPs and hardness ratio).\n"
        "  4. Sub-Threshold Discovery: Detects 136 microflares absent from official NOAA catalogs."
    )
    for p in tf3.paragraphs:
        p.font.name = 'Arial'
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(2)

    # ==========================================
    # SLIDE 4: Features (With 2x2 Image Grid)
    # ==========================================
    print("Modifying Slide 4 (Features)...")
    s4 = prs.slides[3]
    
    # Create clean title shape (deletes placeholder to avoid double title)
    create_clean_title(s4, "List of features offered by the solution", "Features Offered by the Solution", NAVY)
        
    # Create new text box below title on the left side (width reduced to 4.5 to make room for grid)
    content_box4 = s4.shapes.add_textbox(Inches(0.34), Inches(1.35), Inches(4.5), Inches(3.9))
    tf4 = content_box4.text_frame
    tf4.word_wrap = True
    tf4.text = (
        "• Multi-Instrument Ingestion & Harmonization:\n"
        "  Automates calibration and alignment of raw FITS files from SoLEXS and HEL1OS.\n\n"
        "• Real-Time Causal Nowcasting:\n"
        "  Detects solar flare onset, peak, and decay phases using dynamic statistical thresholds.\n\n"
        "• Physics-Informed Predictive Modeling:\n"
        "  Forecasts impending flares 30 minutes in advance using rolling physics-backed precursors.\n\n"
        "• Live Operator Dashboard & Alerts:\n"
        "  Displays live counts, risk probabilities, and color-coded hazard alerts (Green, Yellow, Red)."
    )
    for p in tf4.paragraphs:
        p.font.name = 'Arial'
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(3)
        
    # Ingest 2x2 grid of pictures on the right
    img_grid = [
        ("Solar Low Energy X-ray Spectrometer/output/solexs_plot_zoom.png", Inches(5.1), Inches(1.1), "Figure 1: Telemetry & Nowcast Baseline"),
        ("Solar Low Energy X-ray Spectrometer/output/solexs_event_zoom.png", Inches(7.5), Inches(1.1), "Figure 2: Event Detection Window"),
        ("Solar Low Energy X-ray Spectrometer/output/solexs_plot_20260606.png", Inches(5.1), Inches(3.2), "Figure 3: M-Class Flare (June 6)"),
        ("Solar Low Energy X-ray Spectrometer/output/solexs_threshold_20260606.png", Inches(7.5), Inches(3.2), "Figure 4: Nowcast Threshold Validation")
    ]
    
    for path, left, top, caption in img_grid:
        if os.path.exists(path):
            s4.shapes.add_picture(path, left, top, width=Inches(2.2), height=Inches(1.8))
            cap = s4.shapes.add_textbox(left, top + Inches(1.8), Inches(2.2), Inches(0.25))
            cap.text_frame.text = caption
            for p in cap.text_frame.paragraphs:
                p.font.name = 'Arial'
                p.font.size = Pt(8.5)
                p.font.color.rgb = NAVY
                p.font.bold = True
                p.alignment = PP_ALIGN.CENTER

    # ==========================================
    # SLIDE 5: Process Flow Diagram
    # ==========================================
    print("Modifying Slide 5 (Process Flow)...")
    s5 = prs.slides[4]
    
    # Create clean title shape (deletes placeholder to avoid double title)
    create_clean_title(s5, "Process flow diagram or Use-case", "Process Flow Diagram", NAVY)
        
    # Copy shapes from Slide 6 of BAH_PPT (1).pptx (index 5)
    src_slide_6 = prs_src.slides[5]
    skip_shapes_s6 = ["Google Shape;87;p18", "Google Shape;88;p18"] # skip bg and instruction title
    copied_s6 = copy_shapes_between_slides_smart(src_slide_6, s5, skip_shapes_s6, 5)
    
    # Replace labels with concise text to avoid text box expansion and overlaps
    replacements_s5 = {
        "Satellite": "Aditya-L1\nSpacecraft",
        "Database": "Telemetry\n(SoLEXS/HEL1OS)",
        "Preprocessing Pipeline": "Calibration & Alignment",
        "Model \nArchitecture": "Nowcasting &\nForecasting Model",
        "Predicted Frames": "Alert Levels\n(Low/Med/High)",
        "Input Frames": "Merged Telemetry",
        "Self Supervised Learning": "GOES Calibration",
        "Dashboard": "Operator Dashboard",
        "actual": "actual",
        "predicted": "predicted",
        "* We will add a self supervised learning loop": "* We will scale the pipeline with multi-month archival telemetry and attitude correction for operational deployment."
    }
    for shape in copied_s6:
        if shape.has_text_frame:
            tf = shape.text_frame
            tf.word_wrap = True
            # Maximize margins to prevent early word wraps
            tf.margin_left = Inches(0.01)
            tf.margin_right = Inches(0.01)
            tf.margin_top = Inches(0.01)
            tf.margin_bottom = Inches(0.01)
            
            for k, v in replacements_s5.items():
                if k in tf.text:
                    tf.text = v
                    # Increase width slightly to prevent text clipping
                    shape.width = shape.width + Inches(0.35)
                    for p in tf.paragraphs:
                        p.font.name = 'Arial'
                        p.font.size = Pt(8.5) if "*" in v else Pt(9.5)
                        p.font.color.rgb = TEXT_DARK
                        p.font.bold = True if k != "* We will add a self supervised learning loop" else False
                    break

    # ==========================================
    # SLIDE 6: Wireframes/Mocks (Case Study & Overall Timeseries)
    # ==========================================
    print("Modifying Slide 6 (Wireframes / Case Study)...")
    s6 = prs.slides[5]
    
    # Create clean title shape (deletes placeholder to avoid double title)
    create_clean_title(s6, "Wireframes/Mock diagrams", "Case Study & Validation Results", NAVY)
        
    # Place Case Study details in new content textbox
    content_box6 = s6.shapes.add_textbox(Inches(0.3), Inches(1.35), Inches(5.0), Inches(3.9))
    tf6 = content_box6.text_frame
    tf6.word_wrap = True
    tf6.text = (
        "Case Study & Validation:\n"
        "• Superior Instrument Sensitivity: Aditya-L1 SoLEXS captures faint solar activity due to its low-energy threshold and high spectral resolution.\n"
        "• The June 10 Event: On June 10, 2026, at 23:46 UTC, our causal nowcasting algorithm flagged a highly structured, 679-second duration event.\n"
        "• GOES Catalog Gap: This event is completely absent from the official NOAA GOES flare catalog, confirming its status as a newly discovered microflare.\n"
        "• Scientific Importance: Microflares are critical to solving the coronal heating problem, and their real-time detection validates our dynamic baseline approach.\n\n"
        "Validation Benchmarks Summary:\n"
        "• NOAA GOES Recall: 93.2% (68/73 flares recovered)\n"
        "• Holdout Accuracy: 95.8% (SoLEXS), 80.9% (Fusion)\n"
        "• Lead Warning Time: 4.57 mins (SoLEXS), 7.87 mins (Fusion)\n"
        "• Microflare Discovery: 136 sub-threshold events detected"
    )
    for p in tf6.paragraphs:
        p.font.name = 'Arial'
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(2)
        
    # Ingest stacked pictures on the right
    img_zoom = "Solar Low Energy X-ray Spectrometer/output/solexs_20260610_2346_event.png"
    img_global = "Solar Low Energy X-ray Spectrometer/output/solexs_plot.png"
    
    if os.path.exists(img_zoom):
        s6.shapes.add_picture(img_zoom, Inches(5.5), Inches(1.1), width=Inches(4.1), height=Inches(1.8))
        cap_z = s6.shapes.add_textbox(Inches(5.5), Inches(2.9), Inches(4.1), Inches(0.25))
        cap_z.text_frame.text = "Figure 5: June 10 Microflare Event (Not in NOAA)"
        for p in cap_z.text_frame.paragraphs:
            p.font.name = 'Arial'
            p.font.size = Pt(9)
            p.font.color.rgb = NAVY
            p.font.bold = True
            p.alignment = PP_ALIGN.CENTER
            
    if os.path.exists(img_global):
        s6.shapes.add_picture(img_global, Inches(5.5), Inches(3.2), width=Inches(4.1), height=Inches(1.8))
        cap_g = s6.shapes.add_textbox(Inches(5.5), Inches(5.0), Inches(4.1), Inches(0.25))
        cap_g.text_frame.text = "Figure 6: Telemetry Timeseries (June 1–19, 2026)"
        for p in cap_g.text_frame.paragraphs:
            p.font.name = 'Arial'
            p.font.size = Pt(9)
            p.font.color.rgb = NAVY
            p.font.bold = True
            p.alignment = PP_ALIGN.CENTER

    # ==========================================
    # SLIDE 7: Architecture Diagram (With RandomForest Image)
    # ==========================================
    print("Modifying Slide 7 (Architecture)...")
    s7 = prs.slides[6]
    
    # Create clean title shape (deletes placeholder to avoid double title)
    create_clean_title(s7, "Architecture diagram of the proposed", "Architecture Diagram", NAVY)
        
    # Copy shapes from Slide 8 of BAH_PPT (1).pptx (index 7)
    # skip bg and instruction title, but COPY Picture 2 (which we intercept to replace with RandomForest diagram)
    src_slide_8 = prs_src.slides[7]
    skip_shapes_s8 = ["Google Shape;93;p19", "Google Shape;100;p20"] 
    copied_s8 = copy_shapes_between_slides_smart(src_slide_8, s7, skip_shapes_s8, 7)
    
    # Replace labels with concise text to fit within flowchart shapes
    replacements_s7 = {
        "Input Tensor Shape": "Raw Telemetry",
        "Encoder\n      4–5 down-         sampling blocks": "SoLEXS (Soft X-rays)\nThermal Precursors",
        "Decoder\n 4–5 up-sampling blocks": "HEL1OS (Hard X-rays)\nNon-thermal Precursors",
        "Latent Bottleneck": "Spatio-Temporal\nAlignment",
        "Conditional DDPM": "Physics Precursors\n(Rolling Mean/Std)",
        "Noise Scheduler\nReverse Denoising\nTimestep Embedding\nConditioning": "Spectral Hardness Ratio\n(Neupert Effect)",
        "PiNN Block": "Causal Nowcaster\n(Thresholding)",
        "Ladv​=MSE.(∂I​/ ∂t +u.∂I/ ∂x ​+v. ∂I/ ∂y ​)": "Forecast Target:\nPeak in 30 Min",
        "Temporal Positional Encoding": "Unix Time Integration",
        "Self-Supervised\nLearning": "GOES Benchmarking",
        "GNN": "RandomForest Core\n(Balanced Weights)",
        "Anomaly Detection": "Microflare Discovery",
        "*POC of our idea, developed on limited": "*POC developed on Aditya-L1 telemetry (259,071 overlap timestamps, 16 flares)."
    }
    for shape in copied_s8:
        if shape.has_text_frame:
            tf = shape.text_frame
            tf.word_wrap = True
            # Maximize margins to prevent early word wraps
            tf.margin_left = Inches(0.01)
            tf.margin_right = Inches(0.01)
            tf.margin_top = Inches(0.01)
            tf.margin_bottom = Inches(0.01)
            
            for k, v in replacements_s7.items():
                if k in tf.text:
                    tf.text = v
                    # Increase width slightly to prevent text clipping
                    shape.width = shape.width + Inches(0.35)
                    for p in tf.paragraphs:
                        p.font.name = 'Arial'
                        p.font.size = Pt(8.5) if "overlap" in v else Pt(9.5)
                        p.font.color.rgb = TEXT_DARK
                        p.font.bold = True if "overlap" not in v else False
                    break

    # ==========================================
    # SLIDE 8: Tech Stack & References
    # ==========================================
    print("Modifying Slide 8 (Technologies & References)...")
    s8 = prs.slides[7]
    
    # Create clean title shape (deletes placeholder to avoid double title)
    create_clean_title(s8, "Technologies to be used in the solution", "Technologies & References", NAVY)
        
    # Left column for Tech Stack
    content_box8 = s8.shapes.add_textbox(Inches(0.3), Inches(1.35), Inches(4.7), Inches(3.9))
    tf8_l = content_box8.text_frame
    tf8_l.word_wrap = True
    tf8_l.text = (
        "Technologies Used:\n"
        "• Modeling & Forecasting:\n"
        "  - Scikit-learn (RandomForest Classifier Core)\n"
        "  - Joblib (Model serialization and storage)\n"
        "  - Physics-informed precursor models\n\n"
        "• Data & Preprocessing:\n"
        "  - Astropy (Raw FITS file telemetry processing)\n"
        "  - NumPy & Pandas (Data merging, cleaning, alignment)\n"
        "  - SciPy (Statistical thresholding and nowcasting)\n\n"
        "• Interface & Visualization:\n"
        "  - Streamlit (Interactive operator control dashboard)\n"
        "  - Matplotlib & Seaborn (Scientific plotting)\n"
        "  - Localtunnel (Secure remote dashboard access)\n\n"
        "• Deployment & Scaling:\n"
        "  - Docker (Containerized dashboard deployment)\n"
        "  - Python Virtual Environments (Dependency isolation)"
    )
    for p in tf8_l.paragraphs:
        p.font.name = 'Arial'
        p.font.size = Pt(11)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(2)
        
    # Right column for References
    ref_box = s8.shapes.add_textbox(Inches(5.2), Inches(1.35), Inches(4.5), Inches(3.9))
    ref_tf = ref_box.text_frame
    ref_tf.word_wrap = True
    ref_tf.text = (
        "Scientific References:\n"
        "• ISRO Aditya-L1 Mission Data: Telemetry logs for SoLEXS & HEL1OS instruments.\n"
        "• NOAA Space Weather Prediction Center: GOES X-ray Sensor solar flare catalog.\n"
        "• Sarwade et al., 2025: In-flight calibration and performance of SoLEXS.\n"
        "• Nandi et al., 2025: Hard X-ray diagnostics of solar flares: HEL1OS.\n\n"
        "Next Steps:\n"
        "• Phase 1 Submission: Submit slides to Hack2Skill portal.\n"
        "• Team Review: Share Git repository and Colab notebook.\n"
        "• Model Scaling: Ingest multi-month telemetry and attitude data.\n"
        "• Operational Integration: Connect alerts to ISRO Space Situational Awareness Centre (SSAC)."
    )
    for p in ref_tf.paragraphs:
        p.font.name = 'Arial'
        p.font.size = Pt(10.5)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(2)

    # ==========================================
    # SLIDE 9: Cost
    # ==========================================
    print("Modifying Slide 9 (Cost)...")
    s9 = prs.slides[8]
    
    # Create clean title shape (deletes placeholder to avoid double title)
    create_clean_title(s9, "Estimated implementation cost", "Estimated Implementation Cost", NAVY)
        
    # Copy cost table shapes from Slide 10 of BAH_PPT (1).pptx (index 9)
    src_slide_10 = prs_src.slides[9]
    skip_shapes_s10 = ["Google Shape;111;p22", "Google Shape;112;p22"] # skip bg and instruction title
    copied_s10 = copy_shapes_between_slides_smart(src_slide_10, s9, skip_shapes_s10, 9)
    
    s_table9 = None
    s_total9 = None
    for shape in copied_s10:
        if shape.has_table:
            s_table9 = shape.table
        elif shape.has_text_frame and "= ₹5,85,000" in shape.text_frame.text:
            s_total9 = shape
            
    if s_table9:
        cost_data = [
            ["Item", "Cost (₹)", "Description"],
            ["Telemetry Ingestion & Fusion Pipeline", "₹50,000", "Multi-instrument (SoLEXS & HEL1OS) FITS data alignment."],
            ["Causal Nowcasting Engine", "₹50,000", "Zero-lookahead rolling statistical threshold detector."],
            ["Physics-Informed ML Forecaster", "₹1,00,000", "RandomForest model trained on precursor features."],
            ["Interactive Operator Dashboard", "₹40,000", "Streamlit web interface with real-time risk alerts."],
            ["NOAA GOES Validation System", "₹40,000", "Benchmarking engine for automated cross-validation."],
            ["Local Workstation GPU", "₹1,50,000", "Hardware for training and telemetry hosting."],
            ["Documentation & SOP Handover", "₹30,000", "Operational guidelines for space-weather centers."],
            ["Public Dashboard Deployment", "₹25,000", "Secure public hosting and remote access configuration."]
        ]
        for r_idx, row in enumerate(cost_data):
            for c_idx, val in enumerate(row):
                cell = s_table9.cell(r_idx, c_idx)
                cell.text = val
                for p in cell.text_frame.paragraphs:
                    p.font.name = 'Arial'
                    p.font.size = Pt(10)
                    if r_idx == 0:
                        p.font.bold = True
                        p.font.color.rgb = WHITE
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = NAVY
                    else:
                        p.font.bold = False
                        p.font.color.rgb = TEXT_DARK
                        
    if s_total9:
        s_total9.text_frame.text = "= ₹4,85,000 (Estimated Cost (may vary based on final deployment and resources.))"
        for p in s_total9.text_frame.paragraphs:
            p.font.name = 'Arial'
            p.font.size = Pt(12)
            p.font.bold = True
            p.font.color.rgb = NAVY

    # Save the modified presentation
    print(f"Saving final presentation to: {output_path}")
    prs.save(output_path)
    print("Formatting onto official 10-slide template completed successfully!")

if __name__ == '__main__':
    main()

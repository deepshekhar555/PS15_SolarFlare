import os
import sys
import win32com.client

def export_slides():
    ppt_path = r"d:\PS15_SolarFlare\AdityaL1_SolarFlare_BAH_2026.pptx"
    output_dir = r"d:\PS15_SolarFlare\scratch\slides"
    
    if not os.path.exists(ppt_path):
        print(f"Error: Presentation not found at {ppt_path}")
        sys.exit(1)
        
    os.makedirs(output_dir, exist_ok=True)
    
    print("Launching PowerPoint via COM...")
    try:
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        # Keep it invisible to not disturb the user
        powerpoint.Visible = True 
    except Exception as e:
        print(f"Error launching PowerPoint: {e}")
        sys.exit(1)
        
    print(f"Opening {ppt_path}...")
    try:
        presentation = powerpoint.Presentations.Open(ppt_path, ReadOnly=True, WithWindow=False)
    except Exception as e:
        print(f"Error opening presentation: {e}")
        powerpoint.Quit()
        sys.exit(1)
        
    print("Exporting slides as PNGs...")
    for i, slide in enumerate(presentation.Slides):
        slide_path = os.path.join(output_dir, f"slide_{i+1}.png")
        # Export slide as PNG
        slide.Export(slide_path, "PNG")
        print(f"Exported Slide {i+1} to {slide_path}")
        
    presentation.Close()
    powerpoint.Quit()
    print("Successfully exported all slides!")

if __name__ == "__main__":
    export_slides()

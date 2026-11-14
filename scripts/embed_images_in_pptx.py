import os
from pptx import Presentation
from pptx.util import Inches

SRC_PPT = r"C:\Users\imja3\Downloads\PROJECT.pptx"
OUT_PPT = r"C:\Users\imja3\Downloads\PROJECT_WITH_SCREENSHOTS.pptx"
IMG_DIR = r"c:\Users\imja3\Downloads\ADBMS EXP-9\docs\ppt_screenshots"

prs = Presentation(SRC_PPT)

# Mapping of slides to image insertion coordinates (Left, Top, Width, Height) in Inches
# Based on exact blank frames inspected in each slide:
SLIDE_IMAGE_MAP = {
    # Slide 1: Left portrait frame
    0: {"img": "slide_01.png", "left": 0.0, "top": 0.0, "width": 5.0, "height": 7.5},
    # Slide 2: Right portrait frame
    1: {"img": "slide_02.png", "left": 8.33, "top": 0.0, "width": 5.0, "height": 7.5},
    # Slide 3: Left space next to problem definition text
    2: {"img": "slide_03.png", "left": 0.72, "top": 1.6, "width": 5.8, "height": 5.2},
    # Slide 4: Right portrait frame next to database topology text
    3: {"img": "slide_04.png", "left": 8.33, "top": 0.0, "width": 5.0, "height": 7.5},
    # Slide 7: Left portrait frame next to core algorithms text
    6: {"img": "slide_07.png", "left": 0.0, "top": 0.0, "width": 5.0, "height": 7.5},
    # Slide 8: Main center/bottom area for UI Walkthrough
    7: {"img": "slide_08.png", "left": 0.72, "top": 1.3, "width": 11.89, "height": 5.0},
    # Slide 9: Right side area next to stress test results
    8: {"img": "slide_09.png", "left": 7.8, "top": 2.0, "width": 5.0, "height": 4.5},
    # Slide 10: Right side image box (replacing empty shape)
    9: {"img": "slide_10.png", "left": 8.78, "top": 2.78, "width": 3.83, "height": 3.12},
}

for idx, config in SLIDE_IMAGE_MAP.items():
    slide = prs.slides[idx]
    img_path = os.path.join(IMG_DIR, config["img"])
    if os.path.exists(img_path):
        print(f"Adding {config['img']} to Slide {idx + 1} at ({config['left']}\", {config['top']}\")...")
        slide.shapes.add_picture(
            img_path,
            Inches(config["left"]),
            Inches(config["top"]),
            Inches(config["width"]),
            Inches(config["height"])
        )

prs.save(OUT_PPT)
print(f"Presentation saved successfully to: {OUT_PPT}")

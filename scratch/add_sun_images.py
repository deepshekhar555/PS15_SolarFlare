import os

def add_sun_images():
    path = r"d:\PS15_SolarFlare\dashboard.js"
    if not os.path.exists(path):
        print("Error: dashboard.js not found.")
        return
        
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # 1. CME Sun replacement (1 space indentation)
    cme_target = """ // Sun
 const sunG = cmeCtx.createRadialGradient(sunX, sunY, 4, sunX, sunY, 24);
 sunG.addColorStop(0, '#fff');
 sunG.addColorStop(0.2, '#facc15');
 sunG.addColorStop(0.6, '#f97316');
 sunG.addColorStop(1, 'rgba(0,0,0,0)');
 cmeCtx.fillStyle = sunG;
 cmeCtx.beginPath(); cmeCtx.arc(sunX, sunY, 24, 0, Math.PI * 2); cmeCtx.fill();
 cmeCtx.fillStyle = '#94a3b8';
 cmeCtx.fillText('Sun', sunX - 10, sunY + 36);"""

    cme_replacement = """ // Sun
 if (!window.sunImgObj) {
  window.sunImgObj = new Image();
  window.sunImgObj.src = 'sun_orange.png';
 }
 
 // Sun Glow (behind the image)
 const sunG = cmeCtx.createRadialGradient(sunX, sunY, 5, sunX, sunY, 30);
 sunG.addColorStop(0, 'rgba(249, 115, 22, 0.8)');
 sunG.addColorStop(0.5, 'rgba(249, 115, 22, 0.2)');
 sunG.addColorStop(1, 'rgba(0,0,0,0)');
 cmeCtx.fillStyle = sunG;
 cmeCtx.beginPath(); cmeCtx.arc(sunX, sunY, 30, 0, Math.PI * 2); cmeCtx.fill();

 // Sun Image
 if (window.sunImgObj && window.sunImgObj.complete) {
  cmeCtx.drawImage(window.sunImgObj, sunX - 20, sunY - 20, 40, 40);
 } else {
  // Fallback
  cmeCtx.fillStyle = '#f97316';
  cmeCtx.beginPath(); cmeCtx.arc(sunX, sunY, 20, 0, Math.PI * 2); cmeCtx.fill();
 }
 cmeCtx.fillStyle = '#94a3b8';
 cmeCtx.fillText('Sun', sunX - 10, sunY + 36);"""

    # 2. SEP Sun replacement (1 space indentation)
    sep_target = """ // Sun
 const sunG = sepCtx.createRadialGradient(cx, cy, 3, cx, cy, 22);
 sunG.addColorStop(0, '#fff');
 sunG.addColorStop(0.2, '#facc15');
 sunG.addColorStop(0.5, '#f97316');
 sunG.addColorStop(1, 'rgba(0,0,0,0)');
 sepCtx.fillStyle = sunG;
 sepCtx.beginPath(); sepCtx.arc(cx, cy, 22, 0, Math.PI * 2); sepCtx.fill();"""

    sep_replacement = """ // Sun
 if (!window.sunImgObj) {
  window.sunImgObj = new Image();
  window.sunImgObj.src = 'sun_orange.png';
 }
 
 // Sun Glow (behind the image)
 const sunG = sepCtx.createRadialGradient(cx, cy, 5, cx, cy, 30);
 sunG.addColorStop(0, 'rgba(249, 115, 22, 0.8)');
 sunG.addColorStop(0.5, 'rgba(249, 115, 22, 0.2)');
 sunG.addColorStop(1, 'rgba(0,0,0,0)');
 sepCtx.fillStyle = sunG;
 sepCtx.beginPath(); sepCtx.arc(cx, cy, 30, 0, Math.PI * 2); sepCtx.fill();

 // Sun Image
 if (window.sunImgObj && window.sunImgObj.complete) {
  sepCtx.drawImage(window.sunImgObj, cx - 20, cy - 20, 40, 40);
 } else {
  // Fallback
  sepCtx.fillStyle = '#f97316';
  sepCtx.beginPath(); sepCtx.arc(cx, cy, 20, 0, Math.PI * 2); sepCtx.fill();
 }"""

    replaced_cme = False
    replaced_sep = False
    
    if cme_target in content:
        content = content.replace(cme_target, cme_replacement)
        replaced_cme = True
    elif cme_target.replace("\n", "\r\n") in content:
        content = content.replace(cme_target.replace("\n", "\r\n"), cme_replacement.replace("\n", "\r\n"))
        replaced_cme = True
        
    if sep_target in content:
        content = content.replace(sep_target, sep_replacement)
        replaced_sep = True
    elif sep_target.replace("\n", "\r\n") in content:
        content = content.replace(sep_target.replace("\n", "\r\n"), sep_replacement.replace("\n", "\r\n"))
        replaced_sep = True
        
    if replaced_cme or replaced_sep:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        print(f"Success: CME replaced={replaced_cme}, SEP replaced={replaced_sep}")
    else:
        print("Error: Could not find Sun drawing targets in dashboard.js.")

if __name__ == "__main__":
    add_sun_images()

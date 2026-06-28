import os

def restore_and_update():
    cache_path = r"C:\Users\Welcome\.gemini\antigravity-browser-profile\Default\Cache\Cache_Data\f_000bc3"
    dst_path = r"d:\PS15_SolarFlare\dashboard.js"
    
    if not os.path.exists(cache_path):
        print(f"Error: Cache file {cache_path} not found.")
        return
        
    # Read the clean cache file
    with open(cache_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Define the clean switchTab function as it exists in the cache file
    target = """function switchTab(name,panelId,btn) {
 document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
 document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));
 const panel=document.getElementById(panelId);
 if(panel) panel.classList.add('active');
 if(btn) btn.classList.add('active');
 if(name==='hist') {
  const cur=recentSolexs.slice(-100);
  const padded=Array(100-cur.length).fill(null).concat(cur);
  histChart.data.datasets[0].data=padded;
  histChart.update('none');
 } else if(name==='cme') {
  resizeCmeCanvas();
 }
}"""

    # Define the updated switchTab function
    replacement = """function switchTab(name,panelId,btn) {
 document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
 document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));
 const panel=document.getElementById(panelId);
 if(panel) panel.classList.add('active');
 if(btn) btn.classList.add('active');
 if(name==='hist') {
  const cur=recentSolexs.slice(-100);
  const padded=Array(100-cur.length).fill(null).concat(cur);
  histChart.data.datasets[0].data=padded;
  histChart.update('none');
 } else if(name==='cme') {
  resizeCmeCanvas();
 } else if(name==='sep') {
  resizeSepCanvas();
 } else if(name==='suit') {
  resizeSuitCanvas();
 }
}"""

    # Replace using both LF and CRLF line endings to be absolutely robust
    if target in content:
        content = content.replace(target, replacement)
    elif target.replace("\n", "\r\n") in content:
        content = content.replace(target.replace("\n", "\r\n"), replacement.replace("\n", "\r\n"))
    else:
        print("Error: Clean switchTab function target not found in the cache file.")
        return
        
    # Write the restored and updated content to the workspace
    with open(dst_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print("Success: dashboard.js has been perfectly restored from cache and updated with tab-switching canvas resize triggers!")

if __name__ == "__main__":
    restore_and_update()

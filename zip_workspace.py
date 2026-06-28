import os
import zipfile
import time

def zip_project(output_filename, source_dir):
    start_time = time.time()
    ignored_dirs = {'.venv', '.git', '__pycache__'}
    ignored_files = {output_filename, 'zip_workspace.py'}
    
    print(f"Starting compression of '{source_dir}' into '{output_filename}'...")
    print("Excluding: .venv, .git, __pycache__, and other temporary files.")
    
    zip_count = 0
    file_count = 0
    total_bytes = 0
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to prevent os.walk from entering ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            for file in files:
                if file in ignored_files:
                    continue
                
                full_path = os.path.join(root, file)
                # Compute relative path for the zip file structure
                rel_path = os.path.relpath(full_path, source_dir)
                
                # Exclude temporary or cache files
                if file.endswith('.pyc') or file.endswith('.pyo') or file.endswith('.pyd'):
                    continue
                    
                file_size = os.path.getsize(full_path)
                total_bytes += file_size
                file_count += 1
                
                if file_size > 10 * 1024 * 1024:  # > 10MB
                    print(f"  Adding large file: {rel_path} ({file_size / 1024 / 1024:.2f} MB)")
                
                zipf.write(full_path, rel_path)
                
    elapsed_time = time.time() - start_time
    zip_size = os.path.getsize(output_filename)
    
    print("\nCompression completed successfully!")
    print(f"Total files zipped: {file_count}")
    print(f"Original size: {total_bytes / 1024 / 1024:.2f} MB")
    print(f"Compressed ZIP size: {zip_size / 1024 / 1024:.2f} MB")
    print(f"Time taken: {elapsed_time:.2f} seconds")
    print(f"Saved to: {os.path.abspath(output_filename)}")

if __name__ == '__main__':
    # Use current working directory as source_dir
    src = os.getcwd()
    out = os.path.join(src, "PS15_SolarFlare.zip")
    zip_project(out, src)

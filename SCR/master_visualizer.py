import subprocess
import os

def run_script(path):
    print(f"\n{'='*60}")
    print(f"Running {path}...")
    print(f"{'='*60}")
    try:
        # Use the same python executable as the current one
        import sys
        result = subprocess.run([sys.executable, path], check=True, capture_output=False)
        print(f"Successfully finished {path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {path}: {e}")

if __name__ == "__main__":
    # Get the directory where this script is located
    SCR_DIR = os.path.dirname(os.path.abspath(__file__))
    
    scripts = [
        "prep_city_ceiling_v2.py",
        "kassanjee_correction.py",
        "gamma_site_function.py",
        "supplement_sensitivity.py",
        "build_figure.py",
        "ceiling_figure.py",
        "kassanjee_figure.py",
        "phase1c_v2_figure.py",
        "prep_city_figure.py"
    ]
    
    for script_name in scripts:
        script_path = os.path.join(SCR_DIR, script_name)
        if os.path.exists(script_path):
            run_script(script_path)
        else:
            print(f"Warning: {script_name} not found in {SCR_DIR}.")

    print(f"\nAll visualizations completed. Check the 'Figures/' directory.")

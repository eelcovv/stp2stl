import argparse
import logging
import os
import sys
from pathlib import Path

# --- FreeCAD Path Setup ---
# Tries to locate the FreeCAD root directory in the following order:
# 1. FREECAD_PATH environment variable (pointing to the FreeCAD installation root)
# 2. A hardcoded default path.
# From the root, it adds the /bin and /lib directories to the Python path.

FREECAD_ROOT_PATH = None
FREECAD_PATH_ENV = os.getenv("FREECAD_PATH")

if FREECAD_PATH_ENV and Path(FREECAD_PATH_ENV).is_dir():
    FREECAD_ROOT_PATH = Path(FREECAD_PATH_ENV)
    print(f"INFO: Using FreeCAD path from FREECAD_PATH environment variable: {FREECAD_ROOT_PATH}")
else:
    # IMPORTANT: This path must point to the root of your FreeCAD installation.
    default_path = Path(r"C:\Program Files\FreeCAD 1.0")
    if default_path.is_dir():
        FREECAD_ROOT_PATH = default_path
        print(f"INFO: Using default FreeCAD path: {FREECAD_ROOT_PATH}")

if FREECAD_ROOT_PATH and FREECAD_ROOT_PATH.is_dir():
    bin_path = FREECAD_ROOT_PATH / "bin"
    lib_path = FREECAD_ROOT_PATH / "lib"
    mod_path = FREECAD_ROOT_PATH / "Mod"
    paths_to_add = [str(p) for p in [bin_path, lib_path, mod_path] if p.is_dir()]

    if not paths_to_add:
        print(f"ERROR: Could not find 'bin' or 'lib' directories in {FREECAD_ROOT_PATH}")
        sys.exit(1)

    for path in paths_to_add:
        if path not in sys.path:
            sys.path.append(path)
else:
    # Use a simple print for this critical error, as the logger is not yet configured.
    print("ERROR: Could not find the FreeCAD installation directory.")
    print("Please do one of the following:")
    print("1. Set the 'FREECAD_PATH' environment variable to point to the root directory of your FreeCAD installation.")
    print(r"   Example: set FREECAD_PATH=C:\Program Files\FreeCAD 0.21")
    print("2. Modify the 'default_path' variable in this script to the correct location.")
    sys.exit(1)

try:
    import FreeCAD
    import Import
    import MeshPart
except ImportError:
    print("ERROR: Could not import the FreeCAD modules.")
    print(
        f"Please verify that the path '{FREECAD_ROOT_PATH}' is correct and contains the necessary FreeCAD libraries in its 'bin' and 'lib' subdirectories."
    )
    sys.exit(1)

# --- Conversion Function ---


def convert_step_to_stl(input_filepath: str):
    """
    Converts a single STEP file to STL with specific mesh settings.
    """
    output_filepath = os.path.splitext(input_filepath)[0] + ".stl"
    doc = None  # Initialize doc to None for the finally block

    logging.info(f"Processing file: {input_filepath}...")

    try:
        # 1. Create a new document and import the STEP file into it.
        doc = FreeCAD.newDocument()
        Import.insert(input_filepath, doc.Name)

        # Check if any object was imported
        if not doc.Objects:
            raise RuntimeError("STEP file could not be imported or is empty.")

        # 2. Get the shape from the first imported object.
        # This assumes the STEP file contains at least one object.
        shape = doc.Objects[0].Shape

        # 3. Create the Mesh (Tessellation)
        logging.info("Performing meshing...")
        mesh_object = MeshPart.meshFromShape(
            Shape=shape, LinearDeflection=2, AngularDeflection=0.0872665, Relative=True
        )

        # 4. Export to STL
        logging.info(f"Exporting to: {output_filepath}...")
        mesh_object.write(output_filepath)

        logging.info(f"File successfully converted: {output_filepath}")

    except Exception as e:
        # Use logging.exception to include traceback information in the log
        logging.exception(f"Could not convert file {input_filepath}: {e!s}")

    finally:
        # 5. Clean up by closing the document to free up memory
        if doc:
            logging.info(f"Closing document: {doc.Name}")
            FreeCAD.closeDocument(doc.Name)


# --- Main Execution ---


def main():
    """
    Main function for parsing arguments and calling the conversion.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Setup argument parser
    parser = argparse.ArgumentParser(description="Convert one or more STEP (.stp, .step) files to STL (.stl).")
    parser.add_argument(
        "input_files",
        metavar="FILE",
        nargs="+",
        help="One or more paths to the STEP files to be converted.",
    )
    args = parser.parse_args()

    # Loop over all provided files
    logging.info(f"Number of files to convert: {len(args.input_files)}")
    success_count = 0
    for filepath in args.input_files:
        if not os.path.exists(filepath):
            logging.warning(f"File not found, skipping: {filepath}")
            continue

        # Check if it is a STEP file
        if filepath.lower().endswith((".stp", ".step")):
            convert_step_to_stl(filepath)
            success_count += 1
        else:
            logging.warning(f"File is not a .stp or .step file, skipping: {filepath}")

    logging.info(f"Done. {success_count} out of {len(args.input_files)} files processed.")


if __name__ == "__main__":
    main()

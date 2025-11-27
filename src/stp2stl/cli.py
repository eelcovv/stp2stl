import argparse
import logging
import os
import sys
from pathlib import Path

# --- FreeCAD Path Setup ---
# IMPORTANT: This path must point to the 'bin' directory of your FreeCAD installation.
# The 'Mod' directory is incorrect for loading the core libraries.
FREECAD_BIN_PATH = Path(r"C:/Program Files/FreeCAD 1.0/Mod")

if FREECAD_BIN_PATH.is_dir():
    if str(FREECAD_BIN_PATH) not in sys.path:
        sys.path.append(str(FREECAD_BIN_PATH))
else:
    # Use a simple print for this critical error, as the logger is not yet configured.
    print(f"ERROR: The specified FreeCAD path does not exist: {FREECAD_BIN_PATH}")
    print("Please adjust the FREECAD_BIN_PATH in this script to the correct location.")
    sys.exit(1)

try:
    import MeshPart
    import Part
except ImportError:
    print("ERROR: Could not import the FreeCAD modules.")
    print(f"Please verify that the path '{FREECAD_BIN_PATH}' is correct.")
    sys.exit(1)


def convert_step_to_stl(input_filepath: str):
    """
    Converts a single STEP file to STL with specific mesh settings.
    """
    filename_without_ext, _ = os.path.splitext(input_filepath)
    output_filepath = filename_without_ext + ".stl"

    logging.info(f"Reading file: {input_filepath}...")

    try:
        # 1. Read the STEP file directly into a Shape object
        shape = Part.read(input_filepath)

        # 2. Create the Mesh (Tessellation)
        logging.info("Performing meshing...")
        mesh_object = MeshPart.meshFromShape(
            Shape=shape, LinearDeflection=2, AngularDeflection=0.0872665, Relative=True
        )
        # 3. Export to STL
        logging.info(f"Exporting to: {output_filepath}...")
        mesh_object.write(output_filepath)

        logging.info(f"File successfully converted: {output_filepath}")

    except Exception as e:
        logging.exception(f"Could not convert file {input_filepath}: {e!s}")


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

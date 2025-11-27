import argparse
import logging
import os
import sys
from pathlib import Path

# --- FreeCAD Path Setup ---
# IMPORTANT: This path must point to the 'bin' directory of your FreeCAD installation.
FREECAD_BIN_PATH = Path(r"C:\Program Files\FreeCAD 1.0\bin")

if FREECAD_BIN_PATH.is_dir():
    if str(FREECAD_BIN_PATH) not in sys.path:
        sys.path.append(str(FREECAD_BIN_PATH))
else:
    # Use a simple print for this critical error, as the logger is not yet configured.
    print(f"ERROR: The specified FreeCAD path does not exist: {FREECAD_BIN_PATH}")
    print("Please adjust the FREECAD_BIN_PATH in this script to the correct location.")
    sys.exit(1)

try:
    import FreeCAD
    import Part
    import MeshPart
    import Import
except ImportError:
    print("ERROR: Could not import the FreeCAD modules.")
    print(f"Please verify that the path '{FREECAD_BIN_PATH}' is correct.")
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
            FreeCAD.closeDocument(doc.Name)
            logging.info(f"Closed document: {doc.Name}")


# --- Main Execution ---


def main():
    """
    Main function for parsing arguments and calling the conversion.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Convert one or more STEP (.stp, .step) files to STL (.stl)."
    )
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

import argparse
import glob
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
    import Part
except ImportError:
    print("ERROR: Could not import the FreeCAD modules.")
    print(
        f"Please verify that the path '{FREECAD_ROOT_PATH}' is correct and contains the necessary FreeCAD libraries in its 'bin' and 'lib' subdirectories."
    )
    sys.exit(1)

# --- Conversion Function ---


def convert_step_to_stl(
    input_filepath: str,
    scale_x: float,
    scale_y: float,
    scale_z: float,
    args: argparse.Namespace,
):
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
            raise RuntimeError("STEP file could not be imported or is empty.")  # noqa: TRY003, TRY301

        # 2. Get the shape from the first imported object.
        # This assumes the STEP file contains at least one object.
        shape = doc.Objects[0].Shape

        # 3. Apply scaling if necessary
        if scale_x != 1.0 or scale_y != 1.0 or scale_z != 1.0:
            logging.info(f"Applying scaling: x={scale_x}, y={scale_y}, z={scale_z}")
            matrix = FreeCAD.Base.Matrix(scale_x, 0, 0, 0, 0, scale_y, 0, 0, 0, 0, scale_z, 0, 0, 0, 0, 1)
            shape = shape.transformed(matrix)

        # 4. Create the Mesh (Tessellation)
        logging.info(f"Performing meshing with '{args.mesher}' mesher...")
        if args.mesher == "standard":
            angular_deflection_rad = args.angular_deflection * (3.141592653589793 / 180.0)
            mesh_object = MeshPart.meshFromShape(
                Shape=shape,
                LinearDeflection=args.linear_deflection,
                AngularDeflection=angular_deflection_rad,
                Relative=True,
            )
        elif args.mesher == "mefisto":
            mesh_object = MeshPart.meshFromShape(
                Shape=shape,
                Fineness=args.fineness,
                SecondOrder=args.second_order,
                Optimize=args.optimize,
                AllowQuad=args.allow_quad,
            )
        elif args.mesher == "netgen":
            mesh_object = MeshPart.meshFromShape(
                Shape=shape,
                Tessellator=1,  # Use Netgen
                Fineness=args.fineness,
                SecondOrder=args.second_order,
                Optimize=args.optimize,
                AllowQuad=args.allow_quad,
                CheckChart=args.check_chart,
            )
        else:
            # This should not happen due to 'choices' in argparse
            raise ValueError(f"Unknown mesher: {args.mesher}")


        # 5. Export to STL
        logging.info(f"Exporting to: {output_filepath}...")
        mesh_object.write(output_filepath)

        logging.info(f"File successfully converted: {output_filepath}")

    except Exception:
        # Use logging.exception to include traceback information in the log
        logging.exception(f"Could not convert file {input_filepath}")

    finally:
        # 6. Clean up by closing the document to free up memory
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
        help="One or more paths or glob patterns to the STEP files to be converted.",
    )
    parser.add_argument("--scale", type=float, help="Uniform scaling factor for all axes.")
    parser.add_argument("--scale_x", type=float, help="Scaling factor for the X-axis.")
    parser.add_argument("--scale_y", type=float, help="Scaling factor for the Y-axis.")
    parser.add_argument("--scale_z", type=float, help="Scaling factor for the Z-axis.")
    parser.add_argument(
        "--mm_to_m", action="store_true", help="Apply a uniform scaling factor of 0.001 to convert from mm to m."
    )
    # Mesh settings
    mesher_group = parser.add_argument_group("Meshing settings")
    mesher_group.add_argument(
        "--mesher",
        type=str,
        default="standard",
        choices=["standard", "mefisto", "netgen"],
        help="Meshing algorithm to use. Default is 'standard'.",
    )

    # Standard mesher settings
    standard_group = parser.add_argument_group("Standard mesher settings")
    standard_group.add_argument(
        "--linear_deflection",
        type=float,
        default=10.0,
        help="Linear deflection for meshing (for 'standard' mesher). Default is 10.0 mm",
    )
    standard_group.add_argument(
        "--angular_deflection",
        type=float,
        default=5,
        help="Angular deflection for meshing in degrees (for 'standard' mesher). Default is 5 degrees.",
    )

    # Mefisto mesher settings
    mefisto_group = parser.add_argument_group("Mefisto mesher settings")
    mefisto_group.add_argument(
        "--fineness",
        type=int,
        default=2,
        choices=range(6),
        metavar="[0-5]",
        help="Fineness of the mesh (for 'mefisto' or 'netgen' mesher). 0=Very Coarse, 1=Coarse, 2=Moderate, 3=Fine, 4=Very Fine, 5=User defined. Default is 2.",
    )
    mefisto_group.add_argument(
        "--second_order",
        action="store_true",
        help="Create second-order elements (for 'mefisto' or 'netgen' mesher).",
    )
    mefisto_group.add_argument(
        "--optimize",
        action="store_true",
        help="Optimize the mesh surface (for 'mefisto' or 'netgen' mesher).",
    )
    mefisto_group.add_argument(
        "--allow_quad",
        action="store_true",
        help="Allow quadrilateral elements (for 'mefisto' or 'netgen' mesher).",
    )

    # Netgen mesher settings
    netgen_group = parser.add_argument_group("Netgen mesher settings")
    netgen_group.add_argument(
        "--check_chart",
        action="store_true",
        help="Whether to analyze the model chart ('netgen' mesher).",
    )
    args = parser.parse_args()

    # Determine scaling factors
    if args.mm_to_m:
        scale_x = scale_y = scale_z = 0.001
    else:
        scale_x = scale_y = scale_z = 1.0

    if args.scale is not None:
        scale_x = scale_y = scale_z = args.scale

    if args.scale_x is not None:
        scale_x = args.scale_x
    if args.scale_y is not None:
        scale_y = args.scale_y
    if args.scale_z is not None:
        scale_z = args.scale_z

    # Expand glob patterns
    all_files = []
    for pattern in args.input_files:
        expanded_files = glob.glob(pattern, recursive=True)
        if not expanded_files:
            logging.warning(f"No files matched the pattern: {pattern}")
        all_files.extend(expanded_files)

    # Loop over all found files
    logging.info(f"Number of files to convert: {len(all_files)}")
    success_count = 0
    for filepath in all_files:
        if not os.path.exists(filepath):
            logging.warning(f"File not found, skipping: {filepath}")
            continue

        # Check if it is a STEP file
        if filepath.lower().endswith((".stp", ".step")):
            convert_step_to_stl(
                filepath,
                scale_x,
                scale_y,
                scale_z,
                args,
            )
            success_count += 1
        else:
            logging.warning(f"File is not a .stp or .step file, skipping: {filepath}")

    logging.info(f"Done. {success_count} out of {len(all_files)} files processed.")


if __name__ == "__main__":
    main()

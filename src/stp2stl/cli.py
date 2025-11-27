import os

import MeshPart
import Part


def convert_step_to_stl(input_filepath):
    """
    Converteert een STEP-bestand naar STL met specifieke mesh-instellingen.
    """
    # Controleer of het bestand bestaat
    if not os.path.exists(input_filepath):
        print(f"Fout: Bestand niet gevonden: {input_filepath}")
        return

    # Bepaal de naam van het uitvoerbestand (zelfde pad, maar .stl extensie)
    filename_without_ext = os.path.splitext(input_filepath)[0]
    output_filepath = filename_without_ext + ".stl"

    print(f"Bezig met inlezen: {input_filepath}...")

    try:
        # 1. Lees de STEP file in als een Shape (Geometry)
        # We gebruiken Part.Shape() zodat we geen volledig GUI-document hoeven te openen
        shape = Part.Shape()
        shape.read(input_filepath)

        # 2. Maak de Mesh (Tessellatie)
        # Instellingen overgenomen uit jouw log:
        # LinearDeflection=2, AngularDeflection=0.0872665, Relative=True
        print("Meshing uitvoeren...")
        mesh_object = MeshPart.meshFromShape(
            Shape=shape, LinearDeflection=2, AngularDeflection=0.0872665, Relative=True
        )

        # 3. Exporteer naar STL
        print(f"Exporteren naar: {output_filepath}...")
        mesh_object.write(output_filepath)

        print("Succesvol afgerond!")

    except Exception as e:
        print(f"Er is een fout opgetreden: {e!s}")


# ==========================================
# CONFIGURATIE
# ==========================================

# Pas onderstaande regel aan naar de locatie van je STEP bestand
mijn_bestand = r"C:/Nextcloud/Engineering/Projects/CP2532 - Huizhong 301 conversion/02 Working/TOPAssets/Huizhong301Sponsons/geometry/tanks/SPT_02_PS.step"

# Voer de functie uit
convert_step_to_stl(mijn_bestand)

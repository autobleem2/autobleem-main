"""Orca Slicer process profiles "ABleemStation - ASA" (best quality), "... ASA Base" (the final base: nobody sees it,
so 0.20 mm layers) and "... ASA Prototype" (fast test print) for a Voron Trident 300 (0.4 nozzle, Klipper) set up on
Orca's "MyKlipper 0.4 nozzle" printer.

All inherit "0.20mm Standard @MyKlipper" (Orca's Custom vendor). The quality profile, for the best look of this case:
- 0.16 mm layers (first 0.2), 5 walls = the case's 2.4 mm walls are solid perimeters, arachne for the chamfers
- slower outer wall / top + lower accelerations on visible surfaces, seam at the back (the port side)
- hole + elephant-foot compensation (button holes, inserts, the roof's bed-side edge), precise outer wall
- mouse-ear brim against ASA corner lift, no supports (the parts are designed without them), gyroid 25 %
Use them with a calibrated ASA filament profile (temperatures, flow ratio and shrink come from the filament profile).
Writes the profiles to ../files/orca/. With --install it also copies them into Orca's user folder (never
overwrites one that exists); run that with Orca closed:  python make_orca_profile.py [--install]"""
import json
import os
import sys
import time

NAME = "ABleemStation - ASA"
ORCA = os.path.join(os.environ.get("APPDATA", ""), "OrcaSlicer", "user", "default", "process")
HERE = os.path.dirname(os.path.abspath(__file__))
COPY = os.path.normpath(os.path.join(HERE, "..", "files", "orca"))

P = {
    "from": "User",
    "inherits": "0.20mm Standard @MyKlipper",
    "is_custom_defined": "0",
    "name": NAME,
    "print_settings_id": NAME,
    "version": "2.3.1.10",
    "print_extruder_id": ["1"],
    "print_extruder_variant": ["Direct Drive Standard"],
    # layers + shells
    "layer_height": "0.16",
    "initial_layer_print_height": "0.2",
    "wall_loops": "5",
    "wall_generator": "arachne",
    "top_shell_layers": "6",
    "top_shell_thickness": "1",
    "bottom_shell_layers": "6",
    "bottom_shell_thickness": "1",
    "top_surface_pattern": "monotonicline",
    "bottom_surface_pattern": "monotonic",
    "only_one_wall_top": "1",
    "sparse_infill_density": "25%",
    "sparse_infill_pattern": "gyroid",
    # surface quality
    "seam_position": "back",
    "seam_gap": "10%",
    "precise_outer_wall": "1",
    "outer_wall_speed": "60",
    "inner_wall_speed": "110",
    "top_surface_speed": "60",
    "internal_solid_infill_speed": "120",
    "sparse_infill_speed": "120",
    "gap_infill_speed": "60",
    "bridge_speed": "25",
    "internal_bridge_speed": "95%",
    "overhang_1_4_speed": "40%",
    "overhang_2_4_speed": "30%",
    "overhang_3_4_speed": "25%",
    "overhang_4_4_speed": "15%",
    "default_acceleration": "5000",
    "outer_wall_acceleration": "3000",
    "inner_wall_acceleration": "5000",
    "top_surface_acceleration": "3000",
    "travel_acceleration": "6000",
    "accel_to_decel_enable": "0",
    "travel_speed": "250",
    # dimensions (the fit: holes, inserts, the base in the shell)
    "xy_hole_compensation": "0.1",
    "xy_contour_compensation": "0",
    "elefant_foot_compensation": "0.15",
    # first layers + adhesion (ASA)
    "initial_layer_speed": "40",
    "initial_layer_infill_speed": "70",
    "initial_layer_acceleration": "1500",
    "slow_down_layers": "3",
    "brim_type": "brim_ears",
    "brim_width": "6",
    "brim_ears_max_angle": "125",
    "brim_object_gap": "0.1",
    "skirt_loops": "1",
    "enable_support": "0",
    "exclude_object": "1",
    "reduce_crossing_wall": "1",
}

# the fast prototype: the same fit settings (hole / elephant-foot compensation, the filament's shrink), so a test print
# answers "does it fit"; thicker layers, fewer walls, sparse infill, higher speeds (the filament's max flow caps them)
PROTO = dict(P, **{
    "name": "ABleemStation - ASA Prototype",
    "print_settings_id": "ABleemStation - ASA Prototype",
    "layer_height": "0.24",
    "initial_layer_print_height": "0.24",
    "wall_loops": "3",
    "top_shell_layers": "4",
    "top_shell_thickness": "0.8",
    "bottom_shell_layers": "3",
    "bottom_shell_thickness": "0.7",
    "top_surface_pattern": "monotonicline",
    "sparse_infill_density": "12%",
    "sparse_infill_pattern": "grid",
    "seam_position": "aligned",
    "precise_outer_wall": "0",
    "outer_wall_speed": "150",
    "inner_wall_speed": "220",
    "top_surface_speed": "150",
    "internal_solid_infill_speed": "220",
    "sparse_infill_speed": "250",
    "gap_infill_speed": "150",
    "bridge_speed": "40",
    "default_acceleration": "7000",
    "outer_wall_acceleration": "5000",
    "inner_wall_acceleration": "7000",
    "top_surface_acceleration": "5000",
    "travel_acceleration": "7000",
    "travel_speed": "300",
    "initial_layer_speed": "60",
    "initial_layer_infill_speed": "100",
    "slow_down_layers": "1",
})

# the final base: hidden under the case, so 0.20 mm layers and quicker walls - but the fit settings stay (it sits inside
# the shell, carries the Pi's self-tapping standoffs and the countersunk screws), 4 walls and 20 % gyroid for strength
BASE = dict(P, **{
    "name": "ABleemStation - ASA Base",
    "print_settings_id": "ABleemStation - ASA Base",
    "layer_height": "0.2",
    "initial_layer_print_height": "0.2",
    "wall_loops": "4",
    "top_shell_layers": "5",
    "top_shell_thickness": "1",
    "bottom_shell_layers": "4",
    "bottom_shell_thickness": "0.8",
    "sparse_infill_density": "20%",
    "seam_position": "aligned",
    "outer_wall_speed": "120",
    "inner_wall_speed": "180",
    "top_surface_speed": "120",
    "internal_solid_infill_speed": "180",
    "sparse_infill_speed": "200",
    "gap_infill_speed": "100",
    "bridge_speed": "35",
    "default_acceleration": "6000",
    "outer_wall_acceleration": "4000",
    "inner_wall_acceleration": "6000",
    "top_surface_acceleration": "4000",
    "travel_acceleration": "7000",
    "travel_speed": "300",
    "slow_down_layers": "2",
})

os.makedirs(COPY, exist_ok=True)
install = "--install" in sys.argv
for prof in (P, BASE, PROTO):
    name = prof["name"]
    text = json.dumps(prof, indent=4, ensure_ascii=False) + "\n"
    info = "sync_info = \nuser_id = \nsetting_id = \nbase_id = GP004\nupdated_time = %d\n" % int(time.time())
    targets = [COPY]
    if install:
        if os.path.exists(os.path.join(ORCA, name + ".json")):
            print("in Orca already, left as it is:", name)
        else:
            targets.append(ORCA)
    for folder in targets:
        open(os.path.join(folder, name + ".json"), "w", encoding="utf-8", newline="\n").write(text)
        open(os.path.join(folder, name + ".info"), "w", encoding="utf-8", newline="\n").write(info)
        print("written:", os.path.join(folder, name + ".json"))

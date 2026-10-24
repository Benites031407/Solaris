"""SRM-100 aft closure as it is built up on the bench before it goes into the case:
nozzle holder, graphite insert and its O-ring, the two case O-rings, the phenolic
nozzle insulator and the LDPE nozzle cap.  The 18 M6x10 screws go in through the
case wall, so they are not in this sub-assembly.

Nothing is drawn or placed here: the parts and their transforms are the aft_closure
group of srm_assembly.placements(), so this is the full motor's aft end exactly.
"""

from srm_assembly import placements


def gen_step():
    return {"children": [
        {"path": step, "name": name, "transform": trsf, "use_source_colors": True}
        for group, name, step, trsf in placements()
        if group == "aft_closure" and not name.startswith("bolt_")
    ]}

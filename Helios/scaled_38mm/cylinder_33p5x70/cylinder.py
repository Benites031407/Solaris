from build123d import Cylinder, Align, export_step, export_stl
part = Cylinder(radius=33.5/2, height=70, align=(Align.CENTER, Align.CENTER, Align.MIN))
bb = part.bounding_box()
print("size:", bb.size, "volume mm3:", round(part.volume, 1))
export_step(part, "cylinder_33p5x70.step")
export_stl(part, "cylinder_33p5x70.stl", tolerance=0.01, angular_tolerance=0.1)

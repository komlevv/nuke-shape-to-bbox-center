"""
Roto Shape BBox Center to Transform Track
========================================

This script extracts the animated bounding-box center of a named shape
inside a selected Roto or RotoPaint node in Foundry Nuke, then bakes that
motion into a new Transform node.

How it works
------------
For each frame in the project frame range, the script:
1. Finds the target roto shape by name.
2. Reads all control point positions for that shape.
3. Computes the shape bounding box:
      min_x, max_x, min_y, max_y
4. Computes the bounding-box center:
      cx = (min_x + max_x) / 2
      cy = (min_y + max_y) / 2
5. Converts that absolute position into Transform translate space by
   subtracting half of the project format width and height.
6. Writes the result as animated keys into a new Transform node.

Why the format offset is needed
-------------------------------
Roto point positions are read in image/project space, while a Transform node's
translate is typically centered around the format center. Because of that,
the script subtracts:

    half_width  = project_format.width()  / 2
    half_height = project_format.height() / 2

This makes the generated motion align correctly in the comp without requiring
manual offsets such as -1920 / -1080 for UHD.

Requirements
------------
- Run inside Nuke.
- Select a Roto or RotoPaint node before executing.
- The target shape must exist inside that node.
- The script uses the root/project frame range and project format.

Notes
-----
- The script computes the bounding box from shape control points.
- If the spline uses very few points with large bezier handles, the visual
  curve bounds may differ slightly from the control-point bounds.
- The script does not require the shape to exist on the first frame.
  It evaluates every frame independently.

Usage
-----
1. Select your Roto or RotoPaint node.
2. Set SHAPE_NAME below to the exact shape name.
3. Run the script in Nuke's Script Editor.
4. A new Transform node will be created with baked translate animation.

Author
------
Prepared for GitHub release / pipeline sharing.
"""

import nuke
import nuke.rotopaint as rp

SHAPE_NAME = "Spline_BBOX"


def iter_items(layer):
    """Yield all items recursively from a roto layer tree."""
    for item in layer:
        yield item
        if isinstance(item, rp.Layer):
            for sub in iter_items(item):
                yield sub


def find_shape_by_name(root_layer, name):
    """Find the first roto shape with the exact given name."""
    for item in iter_items(root_layer):
        if isinstance(item, rp.Shape):
            if str(getattr(item, "name", "")) == name:
                return item
    return None


def get_bbox_center(shape, frame):
    """
    Compute the bounding-box center of a shape at a given frame.

    Returns:
        (cx, cy) as floats, or None if no control points were found.
    """
    xs = []
    ys = []

    for pt in shape:
        pos = pt.center.getPosition(frame)
        xs.append(pos[0])
        ys.append(pos[1])

    if not xs:
        return None

    cx = (min(xs) + max(xs)) * 0.5
    cy = (min(ys) + max(ys)) * 0.5
    return cx, cy


def main():
    """Create a Transform node driven by the animated bbox center of a roto shape."""
    node = nuke.selectedNode()
    if node.Class() not in ("Roto", "RotoPaint"):
        raise RuntimeError("Select a Roto or RotoPaint node before running this script.")

    shape = find_shape_by_name(node["curves"].rootLayer, SHAPE_NAME)
    if shape is None:
        raise RuntimeError('Shape not found: "{}"'.format(SHAPE_NAME))

    first_f = int(nuke.root()["first_frame"].value())
    last_f = int(nuke.root()["last_frame"].value())

    project_format = nuke.root()["format"].value()
    half_w = project_format.width() / 2.0
    half_h = project_format.height() / 2.0

    transform_node = nuke.createNode("Transform", inpanel=False)
    transform_node.setName(SHAPE_NAME + "_centerTrack")
    transform_node["translate"].setAnimated(0)
    transform_node["translate"].setAnimated(1)

    for frame in range(first_f, last_f + 1):
        center = get_bbox_center(shape, frame)
        if center is None:
            continue

        cx, cy = center

        tx = cx - half_w
        ty = cy - half_h

        transform_node["translate"].setValueAt(tx, frame, 0)
        transform_node["translate"].setValueAt(ty, frame, 1)

    nuke.message("Done.")


main()

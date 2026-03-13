
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

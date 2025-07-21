#!/usr/bin/env python

__version__ = "2025.7"

import inkex, cmath

from inkex.paths import Line, Path, ZoneClose, Move, Curve
from lxml import etree


def to_complex(segment):
    """
    Treats input path segment as point that is converted to complex number
    """
    x = None
    y = None
    if "C" in str(segment):
        x = segment.x4
        y = segment.y4
    else:
        x = segment.x
        y = segment.y

    return complex(round(x, 2), round(y, 2))


def get_complex_length(segment_point):
    """
    Gets segment converted to complex number and retuns it's length
    """
    r, _phi = cmath.polar(segment_point)
    return r


def get_start_end_points(segments, idx):
    """
    Get start/end poins for a current segment
    Start point will be a previous segment end
    """
    if idx == 0:
        raise ValueError(
            f"Unexpected index {idx} to get start/end. It should've been skipped before"
        )

    closed_path = False
    start = to_complex(segments[idx - 1])
    end = None

    if isinstance(segments[idx], ZoneClose):
        closed_path = True
        end = to_complex(segments[0])
    else:
        end = to_complex(segments[idx])

    return (start, end, closed_path)


class LaserCutJoints(inkex.Effect):

    def add_arguments(self, pars):
        # Common
        pars.add_argument(
            "--jointtype", type=str, default="Both", help="Tab, Slot, or Both"
        )
        pars.add_argument("--numtabs", type=int, default=3, help="Number of tabs/slots")
        pars.add_argument(
            "--side", type=int, default=0, help="Side number to place tabs or slots on"
        )
        pars.add_argument(
            "--edgefeatures", type=inkex.Boolean, default=True, help="Tab in corners"
        )
        pars.add_argument(
            "--flipside",
            type=inkex.Boolean,
            default=True,
            help="Make tabs outside the shape",
        )
        # Materials & Laser
        pars.add_argument(
            "--kerf", type=float, default=0.15, help="Kerf (amount lost by the laser)"
        )
        pars.add_argument(
            "--thickness", type=float, default=3.0, help="Material thickness"
        )
        pars.add_argument(
            "--gapclearance",
            type=float,
            default=0.0,
            help="Material clearance (to compensate unevenness)",
        )
        pars.add_argument("--units", type=str, default="mm", help="Unit of measurement")

        # Hidden
        pars.add_argument("--activetab", default="", help="Tab menu")

    def draw_parallel(self, start, guide_line, distance):
        _, phi = cmath.polar(guide_line)
        r = distance

        result = cmath.rect(r, phi) + start
        return complex(round(result.real, 2), round(result.imag, 2))

    def draw_perpendicular(self, start, guide_line, distance, invert=False):
        _, phi = cmath.polar(guide_line)
        r = distance

        if invert:
            phi += cmath.pi / 2
        else:
            phi -= cmath.pi / 2

        result = cmath.rect(r, phi) + start
        return complex(round(result.real, 2), round(result.imag, 2))

    def draw_slot_box(self, start, guideLine, x_distance, y_distance, kerf, gap):
        r, phi = cmath.polar(guideLine)

        slot_width = y_distance - kerf + gap

        # Kerf expansion
        start += cmath.rect(kerf / 2, phi)
        if self.flipside:
            # start += cmath.rect(kerf/2 , polPhi + (cmath.pi / 2))
            start += cmath.rect(slot_width / -2, phi + (cmath.pi / 2))
        else:
            # start += cmath.rect(kerf/2 , polPhi - (cmath.pi / 2))
            start += cmath.rect(slot_width / -2, phi - (cmath.pi / 2))

        lines = []
        lines.append(["M", [start.real, start.imag]])

        # Horizontal
        r = x_distance
        move = cmath.rect(r - kerf, phi) + start
        lines.append(["L", [move.real, move.imag]])
        start = move

        # Vertical
        r = y_distance
        if self.flipside:
            phi += cmath.pi / 2
        else:
            phi -= cmath.pi / 2

        move = cmath.rect(r + gap - kerf, phi) + start
        lines.append(["L", [move.real, move.imag]])
        start = move

        # Horizontal
        r = x_distance
        if self.flipside:
            phi += cmath.pi / 2
        else:
            phi -= cmath.pi / 2
        move = cmath.rect(r - kerf, phi) + start
        lines.append(["L", [move.real, move.imag]])
        start = move

        lines.append(["Z", []])

        return lines

    def draw_tabs(self, path, line):
        """
        Male tab creation
        """
        start, end, close_path = get_start_end_points(path, line)

        if self.edgefeatures:
            seg_count = (self.numtabs * 2) - 1
            draw_valley = False
        else:
            seg_count = (self.numtabs * 2) + 1
            draw_valley = True

        distance = end - start

        seg_length = get_complex_length(distance)
        if seg_count > 0:
            seg_length = (get_complex_length(distance)) / seg_count

        new_lines = []

        # when handling first line need to set M back
        if isinstance(path[line], Move):
            new_lines.append(["M", [start.real, start.imag]])

        for i in range(seg_count):
            if draw_valley:
                if i == 0 or i == seg_count - 1:
                    length_with_kerf = seg_length - self.kerf / 2
                else:
                    length_with_kerf = seg_length - self.kerf
            else:
                if i == 0 or i == seg_count - 1:
                    length_with_kerf = seg_length + self.kerf / 2
                else:
                    length_with_kerf = seg_length + self.kerf

            # inkex.utils.debug(f'Segment length {i}:{segLengthKerf}')

            if draw_valley == True:
                # We are drawing a valley (recess) here
                draw_valley = False
                # Vertical
                if i != 0:
                    start = self.draw_perpendicular(
                        start, distance, self.thickness + self.kerf / 2, self.flipside
                    )
                new_lines.append(["L", [start.real, start.imag]])
                # Horizontal
                start = self.draw_parallel(start, distance, length_with_kerf)
                new_lines.append(["L", [start.real, start.imag]])
            else:
                # We are drawing a tab here
                draw_valley = True
                # Vertical
                start = self.draw_perpendicular(
                    start, distance, self.thickness + self.kerf / 2, not self.flipside
                )
                new_lines.append(["L", [start.real, start.imag]])
                # Horizontal
                start = self.draw_parallel(start, distance, length_with_kerf)
                new_lines.append(["L", [start.real, start.imag]])

        if self.edgefeatures == True:
            start = self.draw_perpendicular(
                start, distance, self.thickness + self.kerf / 2, self.flipside
            )
            new_lines.append(["L", [start.real, start.imag]])

        if close_path:
            new_lines.append(["Z", []])

        return new_lines

    def draw_slots(self, path, line):
        """
        Female slot creation
        """
        start, end, _ = get_start_end_points(path, line)

        # Use the same logic as draw_tabs for segment count
        numslots = self.numslots
        if self.edgefeatures:
            seg_count = (numslots * 2) - 1
        else:
            seg_count = numslots * 2

        distance = end - start

        # ref_lengh = get_complex_length(distance) - self.kerf
        ref_lengh = get_complex_length(distance)
        try:
            if self.edgefeatures:
                seg_length = ref_lengh / seg_count
            else:
                seg_length = ref_lengh / (seg_count + 1)
        except:
            seg_length = ref_lengh

        if self.edgefeatures:
            # Shift start point repective to kerf
            _, phi = cmath.polar(distance)
            start += cmath.rect(self.kerf / 2, phi)

        new_lines = []

        line_style = str(
            inkex.Style(
                {
                    "stroke": "#FF0000",
                    "fill": "none",
                    "stroke-width": str(max(self.kerf, 0.1)),
                }
            )
        )

        slot_id = self.svg.get_unique_id("slot")
        g = etree.SubElement(self.svg.get_current_layer(), "g", {"id": slot_id})
        for i in range(seg_count):
            ef_even = self.edgefeatures and (i % 2) == 0
            nef_uneven = not self.edgefeatures and (i % 2)

            seg_length_now = seg_length
            if self.edgefeatures and (i == 0 or i == seg_count - 1):
                seg_length_now -= self.kerf / 2

            if ef_even or nef_uneven:
                new_lines = self.draw_slot_box(
                    start,
                    distance,
                    seg_length_now,
                    self.thickness,
                    self.kerf,
                    self.gap,
                )

                line_atts = {
                    "style": line_style,
                    "id": slot_id + str(i) + "-inner-close-tab",
                    "d": str(Path(new_lines)),
                }
                etree.SubElement(g, inkex.addNS("path", "svg"), line_atts)

            # Find next point
            _, phi = cmath.polar(distance)
            r = seg_length_now
            start += cmath.rect(r, phi)

    def convert_to_path(self, elem):
        # Fonction pour convertir un élément en chemin
        d = elem.path.to_arrays()
        path = inkex.PathElement()
        path.path = d
        path.style = elem.style
        return path

    def effect(self):
        # Retrieve parameters
        self.side = self.options.side
        self.numtabs = self.options.numtabs
        self.numslots = self.options.numtabs
        self.thickness = self.svg.unittouu(
            str(self.options.thickness) + self.options.units
        )
        self.kerf = self.svg.unittouu(str(self.options.kerf) + self.options.units)
        self.edgefeatures = self.options.edgefeatures
        self.flipside = self.options.flipside
        self.jointtype = self.options.jointtype
        self.gap = self.svg.unittouu(
            str(self.options.gapclearance) + self.options.units
        )

        # TODO: Remove ?
        self.units = self.options.units

        # Convert selected shapes to paths
        for elem in self.svg.selected.values():
            if elem.tag in [
                inkex.addNS("rect", "svg"),
                inkex.addNS("circle", "svg"),
                inkex.addNS("ellipse", "svg"),
                inkex.addNS("line", "svg"),
                inkex.addNS("polyline", "svg"),
                inkex.addNS("polygon", "svg"),
            ]:
                path = self.convert_to_path(elem)
                self.svg.selected.add(path)
                self.svg.selected.pop(elem)
                elem.getparent().replace(elem, path)

        # Process selected objects
        for id, node in self.svg.selected.items():

            if node.tag == inkex.addNS("path", "svg"):

                p = list(node.path.to_superpath().to_segments())

                # Remove duplicate points
                i = 0
                while i < len(p) - 1:
                    if p[i] == p[i + 1]:
                        del p[i]
                    else:
                        i = i + 1

                # Remove last point if identical to first
                if "l" in str(p[i - 1]).lower():
                    if p[0].x == p[i - 1].x and p[0].y == p[i - 1].y:
                        del p[i - 1]

                # lines = len(path) - 1
                line_idx = self.side % len(p)

                # Skip all non supported segments
                while not (isinstance(p[line_idx], (Line, ZoneClose, Curve))):
                    line_idx += 1
                    if line_idx >= len(p):
                        raise ValueError("No drawable Line or ZoneClose segment found.")

                # Basically this should never happen because first segment is a Move
                # it will be skipped and index will be incremented
                if line_idx == 0:
                    raise ValueError(
                        "Can't read path properly! Try different side number."
                    )

                new_path = []
                if self.jointtype == "tabs":
                    new_path = self.draw_tabs(p, line_idx)
                    final_path = p[:line_idx] + new_path + p[line_idx + 1 :]
                    node.set("d", str(Path(final_path)))
                elif self.jointtype == "slots":
                    new_path = self.draw_slots(p, line_idx)
                else:
                    new_path = self.draw_tabs(p, line_idx)

                    final_path = p[:line_idx] + new_path + p[line_idx + 1 :]
                    node.set("d", str(Path(final_path)))
                    new_path = self.draw_slots(p, line_idx)


if __name__ == "__main__":
    LaserCutJoints().run()

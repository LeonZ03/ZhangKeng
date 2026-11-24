"""Interlocking ceramic roof courses fitted to the dimensioned roof planes."""

from dataclasses import dataclass
from math import ceil, cos, pi, sin

from exterior_geometry import MeshBuilder


@dataclass
class Plane:
    axis: int
    start: float
    end: float
    eave: float
    ridge: float
    height: object

    def point(self, across, uphill):
        return (across, uphill) if self.axis == 0 else (uphill, across)

    def coordinates(self, point):
        return (point[self.axis], point[1 - self.axis])

    def clip_against(self, other):
        low, high = sorted((other.eave, other.ridge))
        return (
            lambda p: p[other.axis] - other.start,
            lambda p: other.end - p[other.axis],
            lambda p: p[1 - other.axis] - low,
            lambda p: high - p[1 - other.axis],
            lambda p: other.height(p[1 - other.axis]) - self.height(p[1 - self.axis]) - 0.0005,
        )


def half_clip(polygon, distance, keep_positive):
    kept = []
    last = polygon[-1]
    sign = 1 if keep_positive else -1
    previous = distance(last) * sign
    for point in polygon:
        current = distance(point) * sign
        if (previous >= 0) != (current >= 0):
            t = previous / (previous - current)
            kept.append(tuple(a + (b - a) * t for a, b in zip(last, point)))
        if current >= 0:
            kept.append(point)
        last, previous = point, current
    return kept


def visible_shapes(polygon, cuts):
    visible = [polygon]
    for region in cuts:
        fragments = []
        for fragment in visible:
            clipping = [tuple(distance(point) for point in fragment) for distance in region]
            if any(max(test) <= 0 for test in clipping):
                fragments.append(fragment)
                continue
            for distance in region:
                outside = half_clip(fragment, distance, False)
                if len(outside) >= 3:
                    fragments.append(outside)
                fragment = half_clip(fragment, distance, True)
                if len(fragment) < 3:
                    break
        visible = fragments
        if not visible:
            break
    return visible


def slope_courses(plane, competitors):
    across_count = ceil((plane.end - plane.start) / 0.253)
    uphill_count = ceil(abs(plane.ridge - plane.eave) / 0.309)
    across_width = (plane.end - plane.start) / across_count
    up = (plane.ridge - plane.eave) / uphill_count
    cuts = [plane.clip_against(other) for other in competitors if other.axis != plane.axis]
    field = MeshBuilder()
    for row in range(uphill_count):
        front = plane.eave + row * up
        back = front + up
        for column in range(across_count):
            left = plane.start + column * across_width
            jitter = ((row * 191 + column * 53) % 137) / 137
            for sub in range(8):
                a = left + across_width * sub / 8
                b = left + across_width * (sub + 1) / 8
                polygon = [plane.point(a, front), plane.point(b, front),
                           plane.point(b, back), plane.point(a, back)]

                def tile_point(p, lip=False):
                    x, y = plane.coordinates(p)
                    c = (x - left) / across_width
                    r = (y - front) / up
                    roll = (1 - cos(c * 2 * pi)) * 0.018 + max(0, 1 - 65 * min(c, 1 - c)) * 0.002
                    offset = 0.031 - r * 0.019 - (0.019 if lip else 0)
                    return (p[0], -p[1], plane.height(y) + roll + offset)

                for visible in visible_shapes(polygon, cuts):
                    points = [tile_point(p) for p in visible]
                    uvs = [(p[0] / 0.83 + jitter, p[1] / 0.83 + jitter) for p in visible]
                    area = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(points, points[1:] + points[:1]))
                    if abs(area) <= 1e-9:
                        continue
                    if area < 0:
                        points.reverse()
                        uvs.reverse()
                        visible.reverse()
                    field.face(points, uvs)
                    for p, q in zip(visible, visible[1:] + visible[:1]):
                        if abs(plane.coordinates(p)[1] - front) < 1e-7 and abs(
                            plane.coordinates(q)[1] - front) < 1e-7:
                            field.face([tile_point(q), tile_point(p), tile_point(p, True), tile_point(q, True)],
                                       [(0, 0.1), (0.1, 0.1), (0.1, 0), (0, 0)])
    return field


def ridge_caps(field, axis, start, end, fixed, height):
    count = ceil((end - start) / 0.33)
    width = (end - start) / count
    for row in range(count):
        points, uv = [], []
        for across in (start + row * width, start + (row + 1) * width - 0.002):
            for span in range(11):
                phase = pi * span / 10
                cross = fixed + 0.116 * cos(phase)
                x, y = (across, cross) if axis == 0 else (cross, across)
                points.append((x, -y, height + 0.035 + 0.077 * sin(phase)))
                uv.append((across, span * 0.026))
        faces = [(i, i + 11, i + 12, i + 1) for i in range(10)]
        if axis == 1:
            faces = [face[::-1] for face in faces]
        field.patch(points, faces, uv, smooth=True)


def refine_roof(scene, parent, heights, ceramic, soffit):
    main_ridge, main_eave = heights["mainRidge"], heights["mainEave"]
    cross_ridge, cross_eave = heights["crossRidge"], heights["crossEave"]
    main_slope = (main_ridge - main_eave) / 4.5

    def main_height(side):
        return lambda y: main_ridge - (4.5 - y) * main_slope * side

    def cross_height(side):
        return lambda x: cross_ridge - (5.9 - x) * (cross_ridge - cross_eave) / 2.4 * side

    planes = [Plane(0, start, end, eave, 4.5, main_height(side))
              for eave, side in [(-0.58, 1), (9.58, -1)]
              for start, end in [(-0.57, 3.54), (8.26, 12.37)]]
    planes.extend([Plane(0, 3.54, 8.26, 0.08, 4.5, main_height(1)),
                   Plane(0, 3.54, 8.26, 7.72, 4.5, main_height(-1)),
                   Plane(1, -0.56, 8.39, 2.92, 5.9, cross_height(1)),
                   Plane(1, -0.56, 8.39, 8.88, 5.9, cross_height(-1))])
    for index, plane in enumerate(planes, 1):
        slope_courses(plane, [other for other in planes if other is not plane]).object(
            scene, parent, f"Glazed ceramic tile slope {index}", ceramic)
    ridge = MeshBuilder()
    # Only the portions of the lower ridge outside the higher cross roof remain visible.
    for start, end in [(-0.61, 5.01), (6.79, 12.41)]:
        ridge_caps(ridge, 0, start, end, 4.5, main_ridge)
    ridge_caps(ridge, 1, -0.61, 8.43, 5.9, cross_ridge)
    ridge.object(scene, parent, "Segmented ceramic ridge caps", ceramic)

    purlins = MeshBuilder()
    for axis, across, wall, peak, eaves, slopes in (
        (0, -0.57, -0.1, 4.5, (-0.58, 9.58), (main_height(1), main_height(-1))),
        (0, 12.37, 11.9, 4.5, (-0.58, 9.58), (main_height(1), main_height(-1))),
        (1, -0.56, -0.1, 5.9, (2.92, 8.88), (cross_height(1), cross_height(-1))),
        (1, 8.39, 7.9, 5.9, (2.92, 8.88), (cross_height(1), cross_height(-1))),
    ):
        for eave, slope in zip(eaves, slopes):
            count = ceil(abs(peak - eave) / 0.74)
            for i in range(count):
                up = eave + (peak - eave) * (i + 0.22) / count
                mid = (across + wall) / 2
                z = slope(up) - 0.147
                if axis == 0:
                    center, angle = (mid, -up, z), 0
                else:
                    center, angle = (up, -mid, z), pi / 2
                purlins.box(center, (abs(across - wall) + 0.03, 0.106, 0.089), angle, bevel=0.008)
    purlins.object(scene, parent, "Exposed timber gable purlins", soffit)

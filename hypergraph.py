"""Deterministic layout for the home-page "research map".

Papers are nodes and research themes are hyperedges. Each theme gets a labeled hub on an
ellipse; each paper is pulled toward the hubs of its themes and pushed away from other
papers. Hyperedges are drawn as padded convex hulls (a polygon with a thick round stroke).
Everything is computed at build time, so the SVG needs no JavaScript to render.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Any

WIDTH, HEIGHT = 640, 420
HUB_RX, HUB_RY = 250, 168
MIN_GAP = 24.0
ITERATIONS = 400
CHAR_W, LABEL_PAD, LABEL_H = 6.4, 14, 24

Point = tuple[float, float]


@dataclass(frozen=True)
class Layout:
    hubs: list[dict[str, Any]]
    nodes: list[dict[str, Any]]
    hulls: list[dict[str, Any]]
    width: int = WIDTH
    height: int = HEIGHT


def _jitter(key: str) -> Point:
    digest = hashlib.sha1(key.encode()).digest()
    return (digest[0] / 255 - 0.5) * 30, (digest[1] / 255 - 0.5) * 30


def convex_hull(points: list[Point]) -> list[Point]:
    """Andrew's monotone chain; returns hull vertices in order."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o: Point, a: Point, b: Point) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[Point] = []
    upper: list[Point] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def layout(topics: list[dict[str, Any]], pubs: list[dict[str, Any]]) -> Layout:
    cx, cy = WIDTH / 2, HEIGHT / 2
    hubs = []
    for i, t in enumerate(topics):
        angle = -math.pi / 2 + 2 * math.pi * i / len(topics)
        label = t.get("short") or t["label"]  # the map has less room than the filter chips
        w = len(label) * CHAR_W + 2 * LABEL_PAD
        x = min(max(cx + HUB_RX * math.cos(angle), w / 2 + 4), WIDTH - w / 2 - 4)
        y = min(max(cy + HUB_RY * math.sin(angle), LABEL_H / 2 + 4), HEIGHT - LABEL_H / 2 - 4)
        hubs.append({"id": t["id"], "label": label, "x": x, "y": y, "w": w, "h": LABEL_H})
    hub_at = {h["id"]: (h["x"], h["y"]) for h in hubs}

    members = [p for p in pubs if any(t in hub_at for t in p.get("topics", []))]
    targets, pos = [], []
    for p in members:
        ts = [hub_at[t] for t in p["topics"] if t in hub_at]
        tx = sum(x for x, _ in ts) / len(ts)
        ty = sum(y for _, y in ts) / len(ts)
        # Single-topic papers sit between their hub and the centre, not on the label.
        if len(ts) == 1:
            tx, ty = tx + (cx - tx) * 0.45, ty + (cy - ty) * 0.45
        jx, jy = _jitter(p["id"])
        targets.append((tx, ty))
        pos.append([tx + jx, ty + jy])

    for step in range(ITERATIONS):
        cool = 1 - step / ITERATIONS
        for i, (tx, ty) in enumerate(targets):
            pos[i][0] += (tx - pos[i][0]) * 0.05
            pos[i][1] += (ty - pos[i][1]) * 0.05
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                dx, dy = pos[j][0] - pos[i][0], pos[j][1] - pos[i][1]
                d = math.hypot(dx, dy) or 0.01
                if d < MIN_GAP:
                    push = (MIN_GAP - d) / 2 * (0.5 + cool)
                    pos[i][0] -= dx / d * push
                    pos[i][1] -= dy / d * push
                    pos[j][0] += dx / d * push
                    pos[j][1] += dy / d * push
            for h in hubs:  # keep nodes off the hub labels
                dx, dy = pos[i][0] - h["x"], pos[i][1] - h["y"]
                if abs(dx) < h["w"] / 2 + 8 and abs(dy) < h["h"] / 2 + 8:
                    pos[i][1] += 3 if dy >= 0 else -3
            pos[i][0] = min(max(pos[i][0], 12), WIDTH - 12)
            pos[i][1] = min(max(pos[i][1], 12), HEIGHT - 12)

    nodes = [{"id": p["id"], "title": p["title"], "year": p.get("year"), "url": p["url"],
              "topics": [t for t in p["topics"] if t in hub_at], "x": round(x, 1), "y": round(y, 1),
              "featured": bool(p.get("featured"))}
             for p, (x, y) in zip(members, pos)]
    hulls = []
    for h in hubs:
        pts = [(n["x"], n["y"]) for n in nodes if h["id"] in n["topics"]] + [(h["x"], h["y"])]
        hull = convex_hull(pts)
        hulls.append({"id": h["id"], "points": " ".join(f"{x:.1f},{y:.1f}" for x, y in hull),
                      "count": len(pts) - 1})
    for h in hubs:
        h["count"] = next(c["count"] for c in hulls if c["id"] == h["id"])
    return Layout(hubs=hubs, nodes=nodes, hulls=hulls)

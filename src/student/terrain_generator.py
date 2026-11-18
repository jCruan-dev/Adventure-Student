"""TODO: generate canonical terrain deterministically from specification and seed."""
from src.api import Terrain, TerrainGenerationSpec, TerrainTopology, GenerationFailure

def _build(rows: int, cols: int, open_tiles: set[tuple[int, int]]) -> Terrain:
    return Terrain(tuple("".join("." if (r, c) in open_tiles else "#" for c in range(cols)) for r in range(rows)))

_STEPS = ((0, 1), (1, 0), (0, -1), (-1, 0))  # right, down, left, up

def _neighbors_in(tile, tiles):
    return sum((tile[0] + dr, tile[1] + dc) in tiles for dr, dc in _STEPS)

def _has_branch(tiles) -> bool:
    return any(_neighbors_in(tile, tiles) > 2 for tile in tiles) # is it 2 or 3?

def _grow_tree(rows: int, cols: int, seed: int) -> set[tuple[int, int]]:
    import random
    rng = random.Random(seed)
    open_tiles = {(rng.randrange(rows), rng.randrange(cols))}
    while len(open_tiles) < rows * cols:
        tile = rng.choice(list(open_tiles))
        dr, dc = rng.choice(_STEPS)
        new_tile = (tile[0] + dr, tile[1] + dc)
        if 0 <= new_tile[0] < rows and 0 <= new_tile[1] < cols:
            open_tiles.add(new_tile)
            if _has_branch(open_tiles):
                open_tiles.remove(new_tile)
    return open_tiles

class TerrainGenerator:
    """Keep state local; identical inputs must also agree across fresh instances."""

    def __init__(self) -> None:
        pass

    def generate_terrain(self, specification: TerrainGenerationSpec, seed: int) -> Terrain:
        # This workbench accepts only its documented public introductory family.
        rng = self._rng(seed)
        rows, cols = specification.rows, specification.cols
        lo, hi = specification.min_open_tiles, specification.max_open_tiles
        topology = specification.topology

        candidate = []
        if topology == TerrainTopology.STRAIGHT_PATH:
            if rows == 1  or cols == 1:
                candidate.append({(r, c) for r in range(rows) for c in range(cols)})
            else:
                candidate.append({(0, c) for c in range(cols)})
                candidate.append({(r, 0) for r in range(rows)})
        elif topology == TerrainTopology.BENT_PATH:
            if rows >= 2 and cols >= 2:
                candidate.append({(0, c) for c in range(cols)} | {(r, cols - 1) for r in range(rows)})
                candidate.append({(r, 0) for r in range(rows)} | {(rows - 1, c) for c in range(cols)})
        elif topology == TerrainTopology.BRANCHING_TREE:
            tree = self._branching_tree(rows, cols, seed)
            if tree is not None:
                return _build(rows, cols, tree)
            raise GenerationFailure(f"Failed to generate branching tree with seed {seed}")
        elif topology == TerrainTopology.GENERAL:
            candidate.append({(r, c) for r in range(rows) for c in range(cols)})
            for open_tiles in candidate:
                if lo <= len(open_tiles) <= hi:
                     return _build(rows, cols, open_tiles)
                else:
                    raise GenerationFailure(f"Failed to generate general terrain with seed {seed}")

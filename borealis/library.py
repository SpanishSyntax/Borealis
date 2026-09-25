"""Smart wallpaper library: indexes images via directories, filename tags, and manifests."""

import collections
import pathlib
import random
import re
from typing import Any, Dict, List, Optional, Set, Union

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".avif"}

# Matches tags in filename: "name[tag1,tag2].jpg" or "name[tag1].png"
BRACKET_TAG_REGEX = re.compile(r"\[([a-zA-Z0-9_,\s-]+)\]")
# Matches double-underscore tags: "name__tag1,tag2.jpg"
UNDERSCORE_TAG_REGEX = re.compile(r"__([a-zA-Z0-9_,-]+)")


class WallpaperItem:
    """Represents a single wallpaper with associated tags and metadata."""

    def __init__(self, path: pathlib.Path, tags: Set[str], weight: float = 1.0) -> None:
        self.path = path.resolve()
        self.tags = {t.strip().lower() for t in tags if t.strip()}
        self.weight = weight

    def matches(self, target_tags: Set[str]) -> bool:
        """Returns True if any of the target tags are present on this wallpaper."""
        return bool(self.tags.intersection(target_tags))

    def __repr__(self) -> str:
        return f"<Wallpaper {self.path.name} tags={list(self.tags)}>"


class WallpaperLibrary:
    """Indexes and queries wallpapers from one or more directories with multiple discovery strategies."""

    def __init__(
        self,
        root_dirs: Union[pathlib.Path, List[pathlib.Path]],
        history_size: int = 10,
    ) -> None:
        if isinstance(root_dirs, (pathlib.Path, str)):
            self.root_dirs = [pathlib.Path(root_dirs).resolve()]
        else:
            self.root_dirs = [pathlib.Path(d).resolve() for d in root_dirs]

        self.items: List[WallpaperItem] = []
        self.history: collections.deque = collections.deque(maxlen=history_size)
        self.refresh()

    def refresh(self) -> None:
        """Re-scan all wallpaper directories and build the combined index."""
        self.items.clear()
        seen_paths: Set[pathlib.Path] = set()

        for root_dir in self.root_dirs:
            if not root_dir.exists() or not root_dir.is_dir():
                continue

            # 1. Read optional manifest: wallpapers.toml or manifest.toml
            manifest_meta: Dict[str, Dict[str, Any]] = {}
            for manifest_name in ("wallpapers.toml", "manifest.toml", "zenith.toml"):
                m_path = root_dir / manifest_name
                if m_path.is_file():
                    try:
                        with open(m_path, "rb") as f:
                            data = tomllib.load(f)
                            for entry in data.get("wallpaper", []):
                                if isinstance(entry, dict) and "file" in entry:
                                    manifest_meta[entry["file"]] = entry
                    except Exception:
                        pass
                    break

            # 2. Walk directory
            for p in root_dir.rglob("*"):
                if not p.is_file() or p.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue

                resolved = p.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)

                tags: Set[str] = set()

                # Strategy A: Directory name as tag (e.g. wallpapers/cosmic_void/image.jpg)
                rel_path = p.relative_to(root_dir)
                if len(rel_path.parts) > 1:
                    for part in rel_path.parts[:-1]:
                        tags.add(part.lower())

                # Strategy B: Filename bracket tags: image[tag1,tag2].jpg
                bracket_match = BRACKET_TAG_REGEX.search(p.stem)
                if bracket_match:
                    for t in bracket_match.group(1).split(","):
                        tags.add(t.strip().lower())

                # Strategy C: Double underscore tags: image__tag1,tag2.jpg
                underscore_match = UNDERSCORE_TAG_REGEX.search(p.stem)
                if underscore_match:
                    for t in underscore_match.group(1).split(","):
                        tags.add(t.strip().lower())

                # Strategy D: Manifest metadata
                weight = 1.0
                meta = manifest_meta.get(p.name) or manifest_meta.get(str(rel_path))
                if meta:
                    for t in meta.get("tags", []):
                        tags.add(str(t).strip().lower())
                    weight = float(meta.get("weight", 1.0))

                # Default tag if empty
                if not tags:
                    tags.add("general")

                self.items.append(WallpaperItem(resolved, tags, weight=weight))

    def select(self, mood: str, tags: Optional[List[str]] = None) -> Optional[pathlib.Path]:
        """Select a wallpaper matching the target mood or tags, avoiding recent repeats."""
        if not self.items:
            return None

        search_tags = {mood.lower()}
        if tags:
            for t in tags:
                search_tags.add(t.lower())

        # Candidates matching target tags
        candidates = [item for item in self.items if item.matches(search_tags)]

        # Fallback layer 1: if no direct match, check flat files at root of each root_dir
        if not candidates:
            candidates = [
                item for item in self.items if any(item.path.parent == rd for rd in self.root_dirs)
            ]

        # Fallback layer 2: all wallpapers
        if not candidates:
            candidates = list(self.items)

        # Filter out recently shown if we have enough candidates
        filtered = [item for item in candidates if item.path not in self.history]
        if not filtered:
            filtered = candidates

        # Weighted random selection
        weights = [item.weight for item in filtered]
        chosen = random.choices(filtered, weights=weights, k=1)[0]

        self.history.append(chosen.path)
        return chosen.path

    def get_tag_counts(self) -> Dict[str, int]:
        """Returns a map of tag names to number of matching wallpapers."""
        counts: collections.Counter = collections.Counter()
        for item in self.items:
            for tag in item.tags:
                counts[tag] += 1
        return dict(counts.most_common())

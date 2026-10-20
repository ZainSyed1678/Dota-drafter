import os
import json
import pickle
from datetime import datetime
from typing import Dict, Tuple, List, Any, Optional

from app.config import settings
from app.logger import get_logger

log = get_logger("dota-api.model-loader")


class ModelStore:
    def __init__(self):
        self.hero_map: Dict[int, str] = {}
        self.heroes_list: List[Dict[str, Any]] = []
        self.matchup_matrix: Dict[Tuple[int, int], float] = {}
        self.matchup_samples: Dict[Tuple[int, int], int] = {}
        self.synergy_matrix: Dict[Tuple[int, int], float] = {}
        self.synergy_samples: Dict[Tuple[int, int], int] = {}
        self.hero_roles: Dict[int, List[str]] = {}
        self.hero_avg_matchup: Dict[int, float] = {}
        self.hero_winrate: Dict[int, float] = {}
        self.combiner_weights: Dict[str, float] = {
            'matchup': 1.5604,
            'synergy': 1.5120,
            'winrate': 0.9607,
            'model': 2.2110,
            'intercept': 0.1035,
        }
        self.ml_model: Any = None
        self.id_to_name: Dict[int, str] = {}
        self.name_to_id: Dict[str, int] = {}
        self.sorted_hero_ids: List[int] = []
        self.hero_to_idx: Dict[int, int] = {}

        self.metadata: Dict[str, Any] = {
            "version": "v2.2.0",
            "loaded_at": None,
            "status": "missing_core_files",
            "files": {},
            "combiner_weights": self.combiner_weights,
            "data_freshness": {},
        }

    def load(self, version: Optional[str] = None) -> bool:
        base_dir = settings.MODEL_DIR
        target_dir = base_dir

        if version:
            cand = os.path.join(base_dir, version)
            if os.path.isdir(cand):
                target_dir = cand
        elif os.path.isdir(base_dir):
            subdirs = [
                d for d in os.listdir(base_dir)
                if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith(".")
                and os.path.exists(os.path.join(base_dir, d, "matchup.pkl"))
            ]
            if subdirs:
                subdirs.sort(reverse=True)
                target_dir = os.path.join(base_dir, subdirs[0])

        log.info(f"Loading model artifacts from {target_dir}")
        temp_files = {}

        def _safe_load(name: str, required: bool = True):
            path = os.path.join(target_dir, name)
            if not os.path.exists(path):
                path = os.path.join(base_dir, name)
                if not os.path.exists(path):
                    if required:
                        raise RuntimeError(f"Required model file missing: {path}")
                    return None

            stat = os.stat(path)
            temp_files[name] = {
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
            with open(path, "rb") as f:
                return pickle.load(f)

        try:
            new_hero_map = _safe_load("hero_map.pkl")
            new_matchup = _safe_load("matchup.pkl")
            new_synergy = _safe_load("synergy.pkl")
            new_roles = _safe_load("roles.pkl")

            new_ml_model = _safe_load("model.pkl", required=False)
            new_matchup_samples = _safe_load("matchup_samples.pkl", required=False) or {}
            new_synergy_samples = _safe_load("synergy_samples.pkl", required=False) or {}
            new_weights = _safe_load("combiner_weights.pkl", required=False) or {}
            new_avg = _safe_load("hero_avg_matchup.pkl", required=False) or {}
            new_winrate = _safe_load("hero_winrate.pkl", required=False) or {}

            # Metadata.json
            meta_path = os.path.join(target_dir, "metadata.json")
            if not os.path.exists(meta_path):
                meta_path = os.path.join(base_dir, "metadata.json")
            disk_meta = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        disk_meta = json.load(f)
                except Exception as e:
                    log.warning(f"Failed to read metadata.json: {e}")

            # Heroes metadata.json
            heroes_meta_path = os.path.join(target_dir, "heroes_metadata.json")
            if not os.path.exists(heroes_meta_path):
                heroes_meta_path = os.path.join(base_dir, "heroes_metadata.json")
            new_heroes_list = []
            if os.path.exists(heroes_meta_path):
                try:
                    with open(heroes_meta_path, "r", encoding="utf-8") as f:
                        new_heroes_list = json.load(f)
                except Exception as e:
                    log.warning(f"Failed to read heroes_metadata.json: {e}")

            # Atomic swap
            self.hero_map = new_hero_map
            self.matchup_matrix = new_matchup
            self.matchup_samples = new_matchup_samples
            self.synergy_matrix = new_synergy
            self.synergy_samples = new_synergy_samples
            self.hero_roles = new_roles
            self.ml_model = new_ml_model
            self.hero_avg_matchup = new_avg
            self.hero_winrate = new_winrate
            if new_weights:
                self.combiner_weights = new_weights

            self.id_to_name = new_hero_map
            self.name_to_id = {v.lower(): k for k, v in new_hero_map.items()}
            self.sorted_hero_ids = sorted(list(new_hero_map.keys()))
            self.hero_to_idx = {h: i for i, h in enumerate(self.sorted_hero_ids)}

            if new_heroes_list:
                self.heroes_list = new_heroes_list
            else:
                self.heroes_list = [
                    {
                        "id": hid,
                        "name": hname,
                        "roles": self.hero_roles.get(hid, ["offlane"]),
                        "attribute": "all",
                        "image_url": f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{hname.lower().replace(' ', '_').replace('-', '')}.png"
                    }
                    for hid, hname in sorted(new_hero_map.items(), key=lambda x: x[1])
                ]

            self.metadata["status"] = "ready"
            self.metadata["loaded_at"] = datetime.now().isoformat()
            self.metadata["model_path"] = target_dir
            self.metadata["files"] = temp_files
            self.metadata["combiner_weights"] = self.combiner_weights
            if disk_meta:
                self.metadata.update(disk_meta)

            log.info(f"Loaded model version {self.metadata.get('version', 'unknown')} ({len(self.hero_map)} heroes)")
            return True

        except Exception as e:
            log.error(f"Error loading models: {e}", exc_info=True)
            self.metadata["status"] = "missing_core_files"
            self.metadata["error"] = str(e)
            return False


store = ModelStore()
store.load()

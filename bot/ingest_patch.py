import os
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333" if os.path.exists("/.dockerenv") else "http://localhost:6333")
COLLECTION_NAME = "patch_notes"

def fetch_hero_patch_notes():
    print("Fetching Dota 2 hero and patch data from OpenDota...")
    heroes_resp = requests.get("https://api.opendota.com/api/constants/heroes").json()
    patches_resp = requests.get("https://api.opendota.com/api/constants/patchnotes").json()
    
    # Map internal names to localized names
    hero_map = {}
    for hid, info in heroes_resp.items():
        clean_name = info['name'].replace("npc_dota_hero_", "")
        hero_map[clean_name] = info['localized_name']
        
    recent_patches = list(patches_resp.keys())[-5:]
    print(f"Aggregating notes across patches: {recent_patches}")
    
    hero_notes = {loc_name: [] for loc_name in hero_map.values()}
    
    for patch in reversed(recent_patches):
        p_data = patches_resp.get(patch, {})
        heroes_data = p_data.get("heroes", {})
        patch_display = patch.replace("_", ".")
        
        for h_key, changes in heroes_data.items():
            if h_key == "misc":
                continue
            loc_name = hero_map.get(h_key, h_key.replace("_", " ").title())
            if loc_name not in hero_notes:
                hero_notes[loc_name] = []
                
            change_lines = []
            if isinstance(changes, dict):
                for ability, clist in changes.items():
                    ability_clean = ability.replace(f"{h_key}_", "").replace("_", " ").title()
                    if isinstance(clist, list):
                        for c in clist:
                            change_lines.append(f"  • {ability_clean}: {c}")
                    else:
                        change_lines.append(f"  • {ability_clean}: {clist}")
            elif isinstance(changes, list):
                for c in changes:
                    change_lines.append(f"  • {c}")
            elif isinstance(changes, str):
                change_lines.append(f"  • {changes}")
                
            if change_lines:
                hero_notes[loc_name].append(f"[Patch {patch_display}]\n" + "\n".join(change_lines))
                
    formatted_docs = []
    for loc_name, notes in hero_notes.items():
        if notes:
            full_text = f"## {loc_name}\n" + "\n\n".join(notes[:3])
        else:
            full_text = f"## {loc_name}\nNo major balance changes in recent patches ({recent_patches[0].replace('_', '.')} to {recent_patches[-1].replace('_', '.')}). Hero stats remain stable."
        
        formatted_docs.append({
            "hero": loc_name,
            "hero_lower": loc_name.lower(),
            "text": full_text
        })
        
    return formatted_docs

def ingest():
    print("Grog connecting to Qdrant...")
    client = QdrantClient(url=QDRANT_URL)
    
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
        print("Dropping existing collection...")
        client.delete_collection(collection_name=COLLECTION_NAME)
    except Exception:
        pass

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print(f"Collection '{COLLECTION_NAME}' created.")

    docs = fetch_hero_patch_notes()
    print(f"Generated patch notes for {len(docs)} Dota heroes!")

    # Save to patch_notes.md for reference
    with open("patch_notes.md", "w", encoding="utf-8") as f:
        f.write("# Dota 2 Comprehensive Patch Notes\n\n")
        for d in docs:
            f.write(d["text"] + "\n\n")

    print("Embedding documents using fastembed (BAAI/bge-small-en-v1.5)...")
    embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    texts = [d["text"] for d in docs]
    embeddings = list(embedding_model.embed(texts))

    points = []
    for i, (doc, vector) in enumerate(zip(docs, embeddings)):
        points.append(
            PointStruct(
                id=i,
                vector=vector.tolist(),
                payload={
                    "hero": doc["hero"],
                    "hero_lower": doc["hero_lower"],
                    "text": doc["text"]
                }
            )
        )

    print(f"Upserting {len(points)} points into Qdrant...")
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    print("Grog successfully loaded patch notes for ALL Dota heroes into Qdrant!")

if __name__ == "__main__":
    ingest()

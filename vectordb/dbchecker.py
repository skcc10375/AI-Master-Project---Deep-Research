import chromadb
import yaml
from box import Box

with open("config.yml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
    config = Box(config)

client = chromadb.PersistentClient(path=config.PERSIST_DIR)
print("collections:", [c.name for c in client.list_collections()])

col = client.get_collection(config.COLLECTION)
print("count:", col.count())

data = col.get(
    include=["metadatas", "documents"], offset=0
)  # ids는 자동 포함, include엔 3가지만 허용
print(data["metadatas"])
# print(data["ids"])
# print(data["documents"])

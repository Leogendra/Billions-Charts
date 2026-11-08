from pymongo import MongoClient
from dotenv import load_dotenv
import sys
import os

load_dotenv()
BATCH_SIZE = 1000
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
if not(MONGO_URI) or not(MONGO_DB_NAME):
    sys.exit("MONGO_URI and MONGO_DB_NAME must be set")




def clone_database():
    source_name = MONGO_DB_NAME
    target_name = f"{MONGO_DB_NAME}_test"

    print(f"Cloning database '{source_name}' into '{target_name}'.")
    input("Press Enter to confirm...")

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    source = client[source_name]
    target = client[target_name]

    for name in source.list_collection_names():
        if name.startswith("system."):
            continue

        # delete all documents in the collection
        target[name].delete_many({})

        batch = []
        count = 0
        for doc in source[name].find():
            batch.append(doc)
            if len(batch) >= BATCH_SIZE:
                target[name].insert_many(batch)
                count += len(batch)
                batch = []
        if batch:
            target[name].insert_many(batch)
            count += len(batch)

        for index in source[name].list_indexes():
            if index["name"] == "_id_":
                continue
            options = {k: v for k, v in index.items() if k in ("unique", "sparse", "expireAfterSeconds")}
            target[name].create_index(list(index["key"].items()), name=index["name"], **options)

        print(f"{name}: {count} docs copied")
    
    print(f"Clone complete. Database '{target_name}' is ready for testing.")




if __name__ == "__main__":
    clone_database()

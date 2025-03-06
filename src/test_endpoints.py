import random

import requests

from fundus_murag.data.vector_db import VectorDB

BASE_URL = "http://localhost:58008/search"
vdb = VectorDB()


def test_endpoint(endpoint, payload=None, files=None):
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.post(url, json=payload, files=files)
        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"Failed {endpoint} with status {response.status_code}: {response.text}"
            )
            return []
    except Exception as e:
        print(f"Error testing {endpoint}: {e}")
        return []


def fetch_random_record():
    records = (
        vdb._get_client()
        .collections.get("FundusRecord")
        .query.fetch_objects(return_properties=["title", "collection_name"], limit=1000)
        .objects
    )
    return random.choice(records) if records else None


def fetch_random_collection():
    collections = (
        vdb._get_client()
        .collections.get("FundusCollection")
        .query.fetch_objects(return_properties=["title"], limit=1000)
        .objects
    )
    return random.choice(collections) if collections else None


################################################################################################
################################################################################################

record_embedding = None
record = fetch_random_record()

# 1. Test /records/image_similarity_search
if record:
    record_embedding = (
        vdb._get_client()
        .collections.get("FundusRecord")
        .query.fetch_object_by_id(uuid=record.uuid, include_vector=True)
    )
    if record_embedding and record_embedding.vector.get("record_image"):
        print(
            f"\nSelected Random Record (Image Similarity Search): {record.properties['title']}"
        )
        results = test_endpoint(
            "/records/image_similarity_search",
            payload={
                "query_embedding": record_embedding.vector["record_image"],
                "search_in_collections": [record.properties.get("collection_name")],
                "top_k": 5,
            },
        )
        for idx, res in enumerate(results, 1):
            certainty = res.get("certainty", "N/A")
            distance = res.get("distance", "N/A")
            print(
                f"{idx}. Title: {res['title']} (Distance: {distance}, Certainty: {certainty})"
            )

################################################################################################
################################################################################################

# 2. Test /records/title_similarity_search
if record:
    if record_embedding and record_embedding.vector.get("record_title"):
        print(
            f"\nSelected Random Record (Title Similarity Search): {record.properties['title']}"
        )
        results = test_endpoint(
            "/records/title_similarity_search",
            payload={
                "query_embedding": record_embedding.vector["record_title"],
                "search_in_collections": [record.properties.get("collection_name")],
                "top_k": 5,
            },
        )
        for idx, res in enumerate(results, 1):
            certainty = res.get("certainty", "N/A")
            distance = res.get("distance", "N/A")
            print(
                f"{idx}. Title: {res['title']} (Distance: {distance}, Certainty: {certainty})"
            )

################################################################################################
################################################################################################

# 3. Test /records/title_lexical_search
if record:
    print(
        f"\nSelected Random Record (Title Lexical Search): {record.properties['title']}"
    )
    results = test_endpoint(
        "/records/title_lexical_search",
        payload={
            "query": record.properties["title"],
            "collection_name": record.properties.get("collection_name"),
            "top_k": 5,
        },
    )
    for idx, res in enumerate(results, 1):
        print(f"{idx}. Title: {res['title']} (Collection: {res['collection_name']})")

################################################################################################
################################################################################################

collection = fetch_random_collection()
collection_embedding = None

# 4. Test /collections/lexical_search
if collection:
    print(
        f"\nSelected Random Collection (Title Lexical Search): {collection.properties['title']}"
    )
    results = test_endpoint(
        "/collections/title_lexical_search",
        payload={
            "query": collection.properties["title"],
            "top_k": 5,
            "search_in_collection_name": True,
            "search_in_title": True,
            "search_in_description": True,
            "search_in_german_title": True,
            "search_in_german_description": True,
        },
    )
    for idx, res in enumerate(results, 1):
        print(
            f"{idx}. Collection Title: {res['title']} (Name: {res['collection_name']})"
        )

################################################################################################
################################################################################################

# 5. Test /collections/title_similarity_search
if collection:
    collection_embedding = (
        vdb._get_client()
        .collections.get("FundusCollection")
        .query.fetch_object_by_id(uuid=collection.uuid, include_vector=True)
    )
    if collection_embedding and collection_embedding.vector.get("collection_title"):
        print(
            f"\nSelected Random Collection (Title Similarity Search): {collection.properties['title']}"
        )
        results = test_endpoint(
            "/collections/title_similarity_search",
            payload={
                "query_embedding": collection_embedding.vector["collection_title"],
                "top_k": 5,
            },
        )
        for idx, res in enumerate(results, 1):
            certainty = res.get("certainty", "N/A")
            distance = res.get("distance", "N/A")
            print(
                f"{idx}. Title: {res['title']} (Distance: {distance}, Certainty: {certainty})"
            )

################################################################################################
################################################################################################

# 6. Test /collections/description_similarity_search
if collection_embedding and collection_embedding.vector.get("collection_description"):
    print(
        f"\nSelected Random Collection (Description Similarity Search): {collection.properties['title']}"
    )
    results = test_endpoint(
        "/collections/description_similarity_search",
        payload={
            "query_embedding": collection_embedding.vector["collection_description"],
            "top_k": 5,
        },
    )
    for idx, res in enumerate(results, 1):
        certainty = res.get("certainty", "N/A")
        distance = res.get("distance", "N/A")
        print(
            f"{idx}. Title: {res['title']} (Distance: {distance}, Certainty: {certainty})"
        )

################################################################################################
################################################################################################


# 7. Test /image_to_image_search
def test_image_to_image_search(endpoint, image_path):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing {endpoint} with image: {image_path}")

    try:
        with open(image_path, "rb") as image_file:
            files = {"file": image_file}
            response = requests.post(url, files=files)

        if response.status_code == 200:
            results = response.json()

            print("\nSearch Results:")
            for idx, item in enumerate(results, 1):
                title = item.get("title", "Unknown Title")
                collection_name = item.get("collection_name", "Unknown Collection")
                print(f"{idx}. {title} (Collection: {collection_name})")
        else:
            print(f"Failed with status code {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError:
        print("Connection Error")
    except FileNotFoundError:
        print(f"Image file not found: {image_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


image_path = "/home/4baba/fundus-murag/src/Amorphophallus_Titanium_roots.jpg"
test_image_to_image_search("/image_to_image_search", image_path)

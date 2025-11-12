import os

import weaviate
from dotenv import load_dotenv
from weaviate.classes.config import Configure
from weaviate.classes.init import Auth

load_dotenv()
# Set up your credentials and API keys
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
huggingface_key = os.getenv("HUGGINGFACE_API_KEY")

headers = {
    "X-HuggingFace-Api-Key": huggingface_key,
}

# Connect to Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    headers=headers,
)

# # Create a collection with Hugging Face vectorizer
# client.collections.create(
#     "DemoCollection",
#     vector_config=[
#         Configure.Vectors.text2vec_huggingface(
#             name="title_vector",
#             source_properties=["title"],
#             model="sentence-transformers/all-MiniLM-L6-v2",
#         )
#     ],
#     # Add properties as needed
# )

# source_objects = [
#     {
#         "title": "The Shawshank Redemption",
#         "description": "A wrongfully imprisoned man forms an inspiring friendship while finding hope and redemption in the darkest of places.",
#     },
#     {
#         "title": "The Godfather",
#         "description": "A powerful mafia family struggles to balance loyalty, power, and betrayal in this iconic crime saga.",
#     },
#     {
#         "title": "The Dark Knight",
#         "description": "Batman faces his greatest challenge as he battles the chaos unleashed by the Joker in Gotham City.",
#     },
#     {
#         "title": "Jingle All the Way",
#         "description": "A desperate father goes to hilarious lengths to secure the season's hottest toy for his son on Christmas Eve.",
#     },
#     {
#         "title": "A Christmas Carol",
#         "description": "A miserly old man is transformed after being visited by three ghosts on Christmas Eve in this timeless tale of redemption.",
#     },
# ]

# collection = client.collections.use("DemoCollection")

# with collection.batch.fixed_size(batch_size=200) as batch:
#     for src_obj in source_objects:
#         # The model provider integration will automatically vectorize the object
#         batch.add_object(
#             properties={
#                 "title": src_obj["title"],
#                 "description": src_obj["description"],
#             },
#             # vector=vector  # Optionally provide a pre-obtained vector
#         )
#         if batch.number_errors > 10:
#             print("Batch import stopped due to excessive errors.")
#             break

# failed_objects = collection.batch.failed_objects
# if failed_objects:
#     print(f"Number of failed imports: {len(failed_objects)}")
#     print(f"First failed object: {failed_objects[0]}")

# client.close()
# print("Weaviate client connection closed.")

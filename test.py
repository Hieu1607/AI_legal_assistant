import os
import sys
import time

import dotenv
import weaviate
from weaviate.agents.query import QueryAgent
from weaviate.classes.init import Auth

dotenv.load_dotenv()

# Add root to sys.path for local imports
root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.append(root)
weaviate_url = os.getenv("WEAVIATE_URL")
api_key = os.getenv("WEAVIATE_API_KEY")

start_time = time.time()
if not weaviate_url or not api_key:
    print("Error: WEAVIATE_URL and WEAVIATE_API_KEY must be set in your environment.")
    print("Please create a .env file and add the following lines:")
    print("WEAVIATE_URL=https://your-cluster-url.weaviate.network")
    print("WEAVIATE_API_KEY=YOUR_WEAVIATE_API_KEY")
    sys.exit(1)
try:
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(api_key),  # type: ignore
    )
except Exception as e:
    print(f"Failed to connect to Weaviate: {e}")
    sys.exit(1)

if client.is_ready():
    print("Connected to Weaviate successfully.")

query = "Tội lừa đảo chiếm đoạt tài sản theo Bộ luật Hình sự Việt Nam được quy định như thế nào?"

weaviate_agent = QueryAgent(  # type: ignore
    client=client,
    collections=["LegalDocument"],
    system_prompt="You are a legal assistant specialized in Vietnamese law.",
)

response = weaviate_agent.ask(query)

if response.sources:
    print("Sources used in the response:")
    for source in response.sources:
        collection = client.collections.get(source.collection)
        obj = collection.query.fetch_object_by_id(source.object_id)
        print(f"Source: {source}, Object: {obj}")
        print(
            "------------------------------------------------------------------------"
        )
        print(
            "------------------------------------------------------------------------"
        )

client.close()

end_time = time.time()

print(response.total_time)


print("----------------------------------------")
print("----------------------------------------")
print(f"Execution time: {end_time - start_time} seconds")

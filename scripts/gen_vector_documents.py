from llama_index.packs.raptor import RaptorPack
import os
import nest_asyncio
nest_asyncio.apply()
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core.schema import Document
from dataset import filepath as fp

def load_file():
    files = os.listdir(fp.SUANMING_DIR)
    paths = []
    for file in files:
        paths.append(os.path.join(fp.SUANMING_DIR, file))
    documents = SimpleDirectoryReader(input_files=paths).load_data()
    return documents

def get_raptor(documents):
    uri = 'http://' + os.environ['Milvus_ip'] + ':' + os.environ['Milvus_port'] + '/'
    vector_store = MilvusVectorStore(uri=uri, collection_name='AI_fortune_v1', dim=1536)
    raptor_pack = RaptorPack(
        documents,
        embed_model=OpenAIEmbedding(
            model="text-embedding-3-small"
        ),  # used for embedding clusters
        llm=OpenAI(model="gpt-4-0125-preview", temperature=0),  # gpt-3.5-turbo，used for generating summaries gpt-4
        vector_store=vector_store,  # used for storage
        similarity_top_k=4,  # top k for each layer, or overall top-k for collapsed
        mode="collapsed",  # sets default mode
        transformations=[
            SentenceSplitter(chunk_size=512, chunk_overlap=128)
        ],  # transformations applied for ingestion
    )

    return raptor_pack


def train():
    documents = load_file()
    get_raptor(documents)


if __name__ == '__main__':
    train()


from typing import List, Union, Generator, Iterator
import os
from pydantic import BaseModel
from llama_index.llms.openai_like import OpenAILike
from llama_index.core import VectorStoreIndex, PromptTemplate
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PyMuPDFReader
import aiohttp
import asyncio
from llama_index.core import Settings

# inside the pipelines container, run:
# pip install llama-index llama-index-core llama-index-llms-openai-like llama-index-readers-file pymupdf


class RAGStringQueryEngine(CustomQueryEngine):
    """RAG String Query Engine."""

    retriever: BaseRetriever
    llm: OpenAILike
    qa_prompt: PromptTemplate

    def custom_query(self, query_str: str):
        nodes = self.retriever.retrieve(query_str)

        context_str = "\n\n".join([n.node.get_content() for n in nodes])
        response = self.llm.complete(
            self.qa_prompt.format(context_str=context_str, query_str=query_str)
        )

        return str(response)


class Pipeline:
    class Valves(BaseModel):
        VLLM_HOST: str
        OPENAI_API_KEY: str
        DOCUMENT_RAG_MODEL: str

    def __init__(self):
        self.name = "New employee guide"

        self.valves = self.Valves(
            **{
                "pipelines": ["*"],
                "VLLM_HOST": os.getenv("VLLM_HOST", "your_vllm_host"),
                "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", 'aaaaa'),
                "DOCUMENT_RAG_MODEL": "mistralai/Mistral-7B-Instruct-v0.3"
            }
        )


        loader = PyMuPDFReader()

        #Enter docement path, put it inside docker container by using external
        #   directory in docker-compose that I have also included
        #   and file path should start with /app/pipelines/
        documents = loader.load(file_path="/app/pipelines/new_worker_guide.pdf")

        #Change embeddings as you wish 
        embed_model = HuggingFaceEmbedding(model_name="intfloat/multilingual-e5-large")

        Settings.embed_model = embed_model

        index = VectorStoreIndex.from_documents(documents)

        self.retriever = index.as_retriever()


    async def on_startup(self):
        pass

    async def on_shutdown(self):
        pass

    async def make_request_with_retry(self, url, params, retries=3, timeout=10):
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=timeout) as response:
                        response.raise_for_status()
                        return await response.text()
                    
            except (aiohttp.ClientResponseError, aiohttp.ClientPayloadError, aiohttp.ClientConnectionError) as e:
                if attempt + 1 == retries:
                    raise

                await asyncio.sleep(2 ** attempt)  # Exponential backoff


    # def handle_streaming_response(self, response_gen):
    #     final_response = ""
    #     for chunk in response_gen:
    #         final_response += chunk
    #     return final_response

    def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Union[str, Generator, Iterator]:

        #find stopping ids for your model
        llm = OpenAILike(
            model=self.valves.DOCUMENT_RAG_MODEL,
            api_base=self.valves.VLLM_HOST,
            api_key=self.valves.OPENAI_API_KEY,
            max_tokens=5000,
            stopping_ids=[50278, 50279, 50277, 1, 0]
        )


        #You can modify this prompt as you wish and 
        qa_prompt = PromptTemplate(
            "Context information is below.\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "You are a helpful AI Assistant providing company specific knowledge to a new employee."
            "Generate human readable output, avoid creating output with gibberish text."
            "Generate only the requested output, don't include any other language before or after the requested output."
            "Use the same language as user does."
            "Never say thank you, that you are happy to help, that you are an AI agent, etc. Just answer directly."
            "Never generate offensive or foul language."
            "Given the context information and not prior knowledge, "
            "answer the query.\n"
            "Query: {query_str}\n"
            "Answer: "
        )


        query_engine = RAGStringQueryEngine(
            retriever=self.retriever,
            llm=llm,
            qa_prompt=qa_prompt,
        )


        try:
            response = query_engine.custom_query(user_message)

            if hasattr(response, 'response_gen'):
                # final_response = self.handle_streaming_response(response.response_gen)
                return str(response)
            else:
                # final_response = response.response
                return str(response)
            

        except aiohttp.ClientPayloadError as e:
            return f"ClientPayloadError: {e}"
        
        except aiohttp.ClientConnectionError as e:
            return f"ClientConnectionError: {e}"

        except aiohttp.ClientResponseError as e:
            return f"ClientResponseError: {e}"
        
        except Exception as e:
            return f"Unexpected error: {e}"

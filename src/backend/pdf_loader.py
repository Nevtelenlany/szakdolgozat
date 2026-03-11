import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google.genai import types
from dotenv import load_dotenv
from google import genai
import os
import chromadb
from backend.db_worker import hatter_mentes, hatter_torles
import multiprocessing

class PDFProcessor:
    def __init__(self):
        #api key
        load_dotenv()
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.client = genai.Client(api_key=self.api_key)
    
    def process_and_store(self, pdf_path, temakor_neve, fajl_neve):

        #szoveg kinyerese
        with fitz.open(pdf_path) as doc:  #documentum megnyitasa
            szoveg = chr(12).join([page.get_text() for page in doc]) #oldalak szovegeinek egy valtozoba val mentese

        #chunking
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_text(szoveg)

        #hosszabb pdf-ek miatt
        vektorok = []
        batch_size = 100 #maximum 100

        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            
            result = self.client.models.embed_content(
                model="gemini-embedding-001", 
                contents=batch_chunks,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            
            vektorok.extend([emb.values for emb in result.embeddings])
            
        #ChromaDB vektorok eltarolasa
        chunk_ids = []
        metaadatok = []
        for x in range(len(chunks)):
            chunk_ids.append(f"{fajl_neve}_chunk_{x}") 
            metaadatok.append({"forras": fajl_neve})
        
        db_path = f"./data/subjects/{temakor_neve}/chroma_db"
        os.makedirs(db_path, exist_ok=True)

        mentes_process = multiprocessing.Process( #folyamat deffinialasa
            target=hatter_mentes, #ezt a függvényt kell lefuttatnia a független folyamatban
            args=(db_path, chunk_ids, vektorok, chunks, metaadatok)#ezeket az argumentumokat varja a függvény
        )
        mentes_process.start()

    def delete_pdf_data(self, temakor_neve, fajl_neve):
        db_path = f"./data/subjects/{temakor_neve}/chroma_db"
        if os.path.exists(db_path):
            torles_process = multiprocessing.Process(
                target=hatter_torles,
                args=(db_path, fajl_neve)
            )
            torles_process.start()
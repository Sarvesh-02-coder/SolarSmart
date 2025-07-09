# solar_chatbot.py
import os
import pathlib
import shutil
import streamlit as st

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ───────────────────────── Configuration ─────────────────────────
GROQ_API_KEY = "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"
PDF_PATH     = "knowledge/solar_guide.pdf"
EMBED_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
INDEX_PATH   = "faiss_index"
# ──────────────────────────────────────────────────────────────────


def build_or_load_index() -> FAISS:
    """Build a FAISS index from `solar_guide.pdf` (first run) or load it later."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    # ── Try loading an existing index ──
    if pathlib.Path(INDEX_PATH).exists():
        return FAISS.load_local(
            INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True   # ← added flag
        )

    # ── Otherwise build it from scratch ──
    if not pathlib.Path(PDF_PATH).exists():
        raise FileNotFoundError(
            f"{PDF_PATH} not found. Put solar_guide.pdf inside a 'knowledge/' folder."
        )

    loader   = PyPDFLoader(PDF_PATH)
    pages    = loader.load_and_split()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks   = splitter.split_documents(pages)

    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(INDEX_PATH)
    return db


def answer_question(question: str, retriever) -> str:
    docs = retriever.get_relevant_documents(question, k=4)
    context = "\n\n".join(d.page_content for d in docs)

    prompt = ChatPromptTemplate.from_template(
        """
        You are a helpful assistant specialised in photovoltaic (solar-panel) topics.
        Answer the user's question using ONLY the context below.
        If the context does not contain the answer, say "I don’t have that information."

        -------------  BEGIN CONTEXT  -------------
        {context}
        -------------  END CONTEXT  ---------------

        Question: {question}
        """
    )

    chain = prompt | ChatGroq(model_name="llama3-8b-8192") | StrOutputParser()
    return chain.invoke({"context": context, "question": question})


def main() -> None:
    st.set_page_config(page_title="🔆 Solar Guide Chatbot", page_icon="🔆")
    st.title("🔆 Ask me anything about solar panels!")

    # Inject Groq key
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

    # Optional sidebar controls
    if st.sidebar.button("Re-build Knowledge Index"):
        shutil.rmtree(INDEX_PATH, ignore_errors=True)
        st.experimental_rerun()

    # Build or load vector store
    with st.spinner("Loading knowledge base…"):
        db = build_or_load_index()
        retriever = db.as_retriever()

    st.success("Knowledge base ready. Ask a question below ⬇️")

    question = st.text_input("Your question:")
    if question:
        with st.spinner("Thinking…"):
            reply = answer_question(question, retriever)
        st.write("**Answer:**")
        st.write(reply)


if __name__ == "__main__":
    pathlib.Path("knowledge").mkdir(exist_ok=True)
    main()

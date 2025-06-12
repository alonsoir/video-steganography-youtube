#!/usr/bin/env python3
"""
Procesador rápido de Moby Dick para embedding y chunking
Para PoC de esteganografía en video
"""

import os
import pickle
import gzip
import requests
import hashlib
import re
from typing import List, Dict, Any
from collections import Counter
import math


def download_moby_dick() -> str:
    """Descarga Moby Dick desde Project Gutenberg"""
    url = "https://www.gutenberg.org/files/2701/2701-0.txt"

    if os.path.exists("moby_dick.txt"):
        print("📖 Moby Dick ya descargado")
        with open("moby_dick.txt", "r", encoding="utf-8") as f:
            return f.read()

    print("⬇️ Descargando Moby Dick...")
    response = requests.get(url)
    text = response.text

    # Limpiar metadata de Gutenberg
    start_marker = "*** START OF THE PROJECT GUTENBERG EBOOK"
    end_marker = "*** END OF THE PROJECT GUTENBERG EBOOK"

    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)

    if start_idx != -1 and end_idx != -1:
        text = text[start_idx:end_idx]

    # Guardar para cache
    with open("moby_dick.txt", "w", encoding="utf-8") as f:
        f.write(text)

    print(f"✅ Descargado: {len(text):,} caracteres")
    return text


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
    """
    Divide el texto en chunks con overlap
    chunk_size pequeño = más QR codes pero más robustez
    """
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if len(chunk.strip()) > 50:  # Evitar chunks muy pequeños
            chunks.append(chunk)

    print(f"📝 Creados {len(chunks)} chunks de ~{chunk_size} palabras")
    return chunks


def create_simple_embeddings(chunks: List[str], vocab_size: int = 1000) -> Dict[str, Any]:
    """
    Crear embeddings simples usando TF-IDF sin dependencias pesadas
    Ultrarrápido y funcional para el PoC
    """
    print("🧠 Creando vocabulario y embeddings simples...")

    # Crear vocabulario de las palabras más frecuentes
    all_words = []
    for chunk in chunks:
        words = re.findall(r'\b[a-zA-Z]+\b', chunk.lower())
        all_words.extend(words)

    word_counts = Counter(all_words)
    vocabulary = [word for word, _ in word_counts.most_common(vocab_size)]
    word_to_idx = {word: idx for idx, word in enumerate(vocabulary)}

    print(f"📚 Vocabulario creado: {len(vocabulary)} palabras únicas")

    # Crear embeddings TF-IDF simples
    embeddings = []
    total_docs = len(chunks)

    # Calcular IDF para cada palabra
    word_doc_counts = {}
    for word in vocabulary:
        count = sum(1 for chunk in chunks if word in chunk.lower())
        word_doc_counts[word] = count

    print("⚡ Generando embeddings TF-IDF...")
    for i, chunk in enumerate(chunks):
        if i % 100 == 0:
            print(f"  Procesando chunk {i + 1}/{len(chunks)}")

        words = re.findall(r'\b[a-zA-Z]+\b', chunk.lower())
        word_counts_chunk = Counter(words)

        # Vector TF-IDF
        embedding = []
        for word in vocabulary:
            tf = word_counts_chunk.get(word, 0) / len(words) if words else 0
            idf = math.log(total_docs / (word_doc_counts[word] + 1))
            tfidf = tf * idf
            embedding.append(tfidf)

        embeddings.append(embedding)

    # Preparar data para QR codes
    data_package = {
        'chunks': chunks,
        'embeddings': embeddings,
        'vocabulary': vocabulary,
        'model_name': 'simple_tfidf',
        'embedding_dim': len(vocabulary),
        'total_chunks': len(chunks),
        'book_title': 'Moby Dick',
        'chunk_size': len(chunks[0].split()) if chunks else 0
    }

    print(f"✅ Embeddings creados: {len(embeddings)} x {len(vocabulary)} dimensiones")
    return data_package


def compress_data(data: Dict[str, Any]) -> bytes:
    """Comprimir datos para QR codes"""
    print("🗜️ Comprimiendo datos...")
    serialized = pickle.dumps(data)
    compressed = gzip.compress(serialized, compresslevel=9)

    print(f"📊 Tamaño original: {len(serialized):,} bytes")
    print(f"📊 Tamaño comprimido: {len(compressed):,} bytes")
    print(f"📊 Ratio compresión: {len(compressed) / len(serialized):.2%}")

    return compressed


def save_data_package(data: Dict[str, Any], filename: str = "moby_dick_embeddings.pkl.gz"):
    """Guardar paquete de datos"""
    compressed = compress_data(data)

    with open(filename, 'wb') as f:
        f.write(compressed)

    print(f"💾 Guardado en: {filename}")
    return compressed


def main():
    print("🚀 Procesando Moby Dick para esteganografía...")

    # 1. Descargar texto
    text = download_moby_dick()

    # 2. Crear chunks pequeños (para QR codes)
    chunks = chunk_text(text, chunk_size=200, overlap=30)

    # 3. Generar embeddings (sin dependencias pesadas)
    data_package = create_simple_embeddings(chunks)

    # 4. Comprimir y guardar
    compressed_data = save_data_package(data_package)

    print("\n✅ Proceso completado!")
    print(f"📈 Total chunks: {len(chunks)}")
    print(f"📏 Dimensión embeddings: {data_package['embedding_dim']}")
    print(f"💾 Datos comprimidos: {len(compressed_data):,} bytes")

    # Calcular cuántos QR codes necesitamos
    max_qr_bytes = 2000  # Aprox capacidad de QR code
    num_qr_codes = (len(compressed_data) + max_qr_bytes - 1) // max_qr_bytes
    print(f"📱 QR codes necesarios: ~{num_qr_codes}")


if __name__ == "__main__":
    main()
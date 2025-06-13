#!/usr/bin/env python3
"""
Sistema RAG completo para Moby Dick extraído de video
Demuestra funcionalidad completa de consultas sobre dataset embebido
"""

import pickle
import gzip
import numpy as np
from typing import List, Dict, Any, Tuple
import re
from collections import Counter
import math


class MobyDickRAG:
    def __init__(self, data_file: str = "moby_dick_embeddings.pkl.gz"):
        """Inicializar sistema RAG desde datos extraídos del video"""
        """recovered_moby_dick_calibrated.pkl.gz"""
        print("🐋 Iniciando Sistema RAG de Moby Dick")
        print("📖 Cargando datos extraídos del video...")

        try:
            with open(data_file, 'rb') as f:
                compressed_data = f.read()

            # Descomprimir y cargar dataset
            decompressed = gzip.decompress(compressed_data)
            self.dataset = pickle.loads(decompressed)

            self.chunks = self.dataset['chunks']
            self.embeddings = np.array(self.dataset['embeddings'])
            self.vocabulary = self.dataset.get('vocabulary', [])
            self.model_name = self.dataset.get('model_name', 'unknown')

            print(f"✅ Dataset cargado exitosamente:")
            print(f"   📚 {len(self.chunks)} chunks de texto")
            print(f"   🧠 {len(self.embeddings)} embeddings ({self.embeddings.shape[1]} dimensiones)")
            print(f"   📝 Vocabulario: {len(self.vocabulary)} palabras")
            print(f"   🔧 Modelo: {self.model_name}")
            print(f"   📖 Libro: {self.dataset.get('book_title', 'Desconocido')}")

        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {data_file}")
            print("💡 Primero ejecuta la extracción del video con:")
            print("   python decode/calibrated_extractor.py video_opacity_X.mp4")
            raise
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            raise

    def create_query_embedding(self, query: str) -> np.ndarray:
        """Crear embedding para query usando mismo método que el dataset"""

        if self.model_name == 'simple_tfidf':
            return self._create_tfidf_embedding(query)
        else:
            print("⚠️ Método de embedding no reconocido, usando TF-IDF simple")
            return self._create_tfidf_embedding(query)

    def _create_tfidf_embedding(self, text: str) -> np.ndarray:
        """Crear embedding TF-IDF para texto de consulta"""

        # Extraer palabras del query
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        word_counts = Counter(words)

        # Crear vector TF-IDF
        embedding = []
        total_docs = len(self.chunks)

        for word in self.vocabulary:
            # TF en el query
            tf = word_counts.get(word, 0) / len(words) if words else 0

            # IDF calculado desde el dataset
            doc_count = sum(1 for chunk in self.chunks if word in chunk.lower())
            idf = math.log(total_docs / (doc_count + 1))

            tfidf = tf * idf
            embedding.append(tfidf)

        return np.array(embedding)

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calcular similaridad coseno entre dos vectores"""

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Buscar chunks más relevantes para la consulta"""

        print(f"🔍 Buscando: '{query}'")

        # Crear embedding del query
        query_embedding = self.create_query_embedding(query)

        # Calcular similaridades
        similarities = []
        for i, chunk_embedding in enumerate(self.embeddings):
            similarity = self.cosine_similarity(query_embedding, chunk_embedding)
            similarities.append((i, similarity))

        # Ordenar por similaridad
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Retornar top-k resultados
        results = []
        for i, (chunk_idx, score) in enumerate(similarities[:top_k]):
            chunk_text = self.chunks[chunk_idx]
            results.append((chunk_text, score))

        return results

    def answer_question(self, question: str, context_size: int = 3) -> str:
        """Responder pregunta usando contexto del libro"""

        print(f"\n❓ Pregunta: {question}")
        print("=" * 60)

        # Buscar chunks relevantes
        results = self.search(question, top_k=context_size)

        if not results:
            return "❌ No se encontraron resultados relevantes."

        # Construir respuesta con contexto
        response = f"📖 **Respuesta basada en Moby Dick extraído del video:**\n\n"

        for i, (chunk, score) in enumerate(results):
            response += f"**Fragmento {i + 1}** (relevancia: {score:.3f}):\n"
            response += f'"{chunk.strip()}"\n\n'

        # Análisis simple de la respuesta
        all_text = " ".join([chunk for chunk, _ in results])
        response += f"**📊 Estadísticas del contexto encontrado:**\n"
        response += f"- Palabras en contexto: {len(all_text.split())}\n"
        response += f"- Fragmentos analizados: {len(results)}\n"
        response += f"- Relevancia promedio: {np.mean([score for _, score in results]):.3f}\n"

        return response

    def interactive_demo(self):
        """Demo interactivo del sistema RAG"""

        print("\n🐋 SISTEMA RAG INTERACTIVO - MOBY DICK")
        print("📖 Extraído exitosamente del video con QR codes invisibles")
        print("=" * 60)
        print("💡 Ejemplos de preguntas:")
        print("   - What is the white whale?")
        print("   - Who is Ahab?")
        print("   - Tell me about the Pequod")
        print("   - What happens to Ishmael?")
        print("   - Describe the whale")
        print("\n🔍 Escribe 'quit' para salir")
        print("=" * 60)

        while True:
            try:
                question = input("\n❓ Tu pregunta: ").strip()

                if question.lower() in ['quit', 'exit', 'salir', 'q']:
                    print("👋 ¡Gracias por usar el sistema RAG de Moby Dick!")
                    break

                if not question:
                    continue

                # Procesar pregunta
                answer = self.answer_question(question)
                print(answer)

            except KeyboardInterrupt:
                print("\n👋 ¡Gracias por usar el sistema RAG!")
                break
            except Exception as e:
                print(f"❌ Error procesando pregunta: {e}")

    def demo_questions(self):
        """Demostrar funcionalidad con preguntas predefinidas"""

        demo_questions = [
            "What is the white whale?",
            "Who is Captain Ahab?",
            "Tell me about Ishmael",
            "What is the Pequod?",
            "Describe the whale hunting"
        ]

        print("\n🎭 DEMOSTRACIÓN AUTOMÁTICA DEL SISTEMA RAG")
        print("=" * 60)

        for question in demo_questions:
            answer = self.answer_question(question)
            print(answer)
            print("\n" + "=" * 60 + "\n")

            # Pausa para lectura
            input("⏸️ Presiona Enter para continuar...")


def main():
    """Demo principal del sistema RAG"""

    try:
        # Inicializar sistema RAG
        rag = MobyDickRAG()

        print("\n🎯 ¡SISTEMA RAG FUNCIONAL!")
        print("🚨 VULNERABILIDAD COMPLETAMENTE DEMOSTRADA:")
        print("   ✅ Dataset completo embebido en video")
        print("   ✅ Datos extraídos exitosamente")
        print("   ✅ Sistema RAG funcional y operativo")
        print("   ✅ Consultas complejas sobre contenido oculto")

        # Menú de opciones
        while True:
            print("\n🔍 Opciones disponibles:")
            print("  1. Demo automático con preguntas predefinidas")
            print("  2. Modo interactivo (haz tus propias preguntas)")
            print("  3. Estadísticas del dataset")
            print("  4. Salir")

            choice = input("\n⭐ Elige una opción (1-4): ").strip()

            if choice == '1':
                rag.demo_questions()
            elif choice == '2':
                rag.interactive_demo()
            elif choice == '3':
                print(f"\n📊 ESTADÍSTICAS DEL DATASET EXTRAÍDO:")
                print(f"   📚 Total chunks: {len(rag.chunks)}")
                print(f"   🧠 Dimensiones embedding: {rag.embeddings.shape}")
                print(f"   📝 Vocabulario: {len(rag.vocabulary)} palabras")
                print(f"   📖 Libro: {rag.dataset.get('book_title', 'Desconocido')}")
                print(f"   🔧 Modelo: {rag.model_name}")

                # Mostrar muestra de contenido
                print(f"\n📝 Muestra del contenido extraído:")
                for i, chunk in enumerate(rag.chunks[:3]):
                    print(f"   Chunk {i + 1}: {chunk[:100]}...")

            elif choice == '4':
                print("👋 ¡Gracias por probar el sistema RAG!")
                break
            else:
                print("❌ Opción no válida")

    except Exception as e:
        print(f"❌ Error en demo principal: {e}")
        print("\n💡 Asegúrate de haber ejecutado primero:")
        print("   python decode/calibrated_extractor.py video_opacity_X.mp4")


if __name__ == "__main__":
    main()
# Video Steganography with QR and YouTube

Este es un experimento ético y educativo para explorar cómo se puede ocultar contenido (como una novela completa) dentro de un vídeo usando códigos QR.

## Objetivo

1. Codificar un libro completo (como *Moby Dick*) en fragmentos de QR visibles en frames de vídeo.
2. Subir el vídeo a YouTube y comprobar si el contenido embebido sobrevive al reencoding.
3. Desarrollar un decodificador que permita reconstruir el mensaje original desde un vídeo local o en línea.
4. Usar el resultado como fuente para un sistema RAG (Retriever-Augmented Generation).

## Instalación

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

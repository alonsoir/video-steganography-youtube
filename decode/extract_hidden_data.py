#!/usr/bin/env python3
"""
Sistema de extracción de QR codes invisibles de video
Recupera completamente Moby Dick embebido con sistema RAG
Para demostrar vulnerabilidad completa en YouTube
"""

import cv2
import numpy as np
import pickle
import gzip
import base64
from pyzbar import pyzbar
from PIL import Image
import hashlib
from typing import List, Dict, Any, Optional, Tuple
import os


class QRExtractor:
    def __init__(self):
        """Inicializar extractor de QR codes invisibles"""
        self.extracted_fragments = {}
        self.total_fragments = None
        self.opacity_threshold = 10  # Umbral para detectar diferencias sutiles

    def enhance_invisible_qr(self, frame: np.ndarray, region: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Mejorar QR invisible para detección
        Amplifica las diferencias sutiles de 1-3 RGB
        """
        x, y, w, h = region

        # Extraer región
        qr_region = frame[y:y + h, x:x + w].copy()

        # Convertir a escala de grises para análisis
        gray = cv2.cvtColor(qr_region, cv2.COLOR_BGR2GRAY)

        # Detectar patrones sutiles
        # Los QR invisibles tienen valores como 3,3,3 (casi negro) y 252,252,252 (casi blanco)

        # Crear máscara para valores "casi negros" (0-10)
        mask_dark = gray < 10

        # Crear máscara para valores "casi blancos" (245-255)
        mask_light = gray > 245

        # Amplificar contraste si detectamos patrón QR
        if np.sum(mask_dark) > 100 and np.sum(mask_light) > 100:
            enhanced = qr_region.copy()
            enhanced[mask_dark] = [0, 0, 0]  # Negro puro
            enhanced[mask_light] = [255, 255, 255]  # Blanco puro
            return enhanced

        return None

    def scan_frame_for_qrs(self, frame: np.ndarray, qr_size: int = 100) -> List[bytes]:
        """
        Escanear frame completo buscando QR codes invisibles
        """
        found_qrs = []
        height, width = frame.shape[:2]

        # Escanear en grid con overlap
        step_size = qr_size // 2

        for y in range(0, height - qr_size, step_size):
            for x in range(0, width - qr_size, step_size):

                # Intentar extraer QR de esta región
                enhanced_qr = self.enhance_invisible_qr(frame, (x, y, qr_size, qr_size))

                if enhanced_qr is not None:
                    # Intentar decodificar QR
                    qr_data = self.decode_qr_from_image(enhanced_qr)
                    if qr_data:
                        found_qrs.append(qr_data)

        return found_qrs

    def decode_qr_from_image(self, qr_image: np.ndarray) -> Optional[bytes]:
        """
        Decodificar QR code desde imagen mejorada
        """
        try:
            # Convertir a PIL Image para pyzbar
            pil_image = Image.fromarray(cv2.cvtColor(qr_image, cv2.COLOR_BGR2RGB))

            # Intentar decodificar
            decoded_objects = pyzbar.decode(pil_image)

            for obj in decoded_objects:
                # Decodificar desde base64
                try:
                    b64_data = obj.data.decode('ascii')
                    decoded_data = base64.b64decode(b64_data)
                    return decoded_data
                except Exception:
                    continue

        except Exception as e:
            pass

        return None

    def parse_fragment(self, fragment_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parsear fragmento extraído y verificar integridad
        """
        try:
            # Buscar separador
            separator = b'|SEPARATOR|'
            if separator not in fragment_data:
                return None

            metadata_bytes, data_bytes = fragment_data.split(separator, 1)

            # Deserializar metadata
            metadata = pickle.loads(metadata_bytes)

            # Verificar checksum
            if hash(data_bytes) != metadata['checksum']:
                print(f"⚠️ Checksum mismatch en fragmento {metadata['idx']}")
                return None

            return {
                'index': metadata['idx'],
                'total': metadata['total'],
                'size': metadata['size'],
                'data': data_bytes
            }

        except Exception as e:
            print(f"⚠️ Error parseando fragmento: {e}")
            return None

    def extract_from_video(self, video_path: str) -> bool:
        """
        Extraer todos los QR codes del video
        """
        print(f"🎬 Analizando video: {video_path}")

        if not os.path.exists(video_path):
            print(f"❌ Video no encontrado: {video_path}")
            return False

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        print(f"📊 Video: {total_frames} frames a {fps:.1f} FPS")
        print("🔍 Buscando QR codes invisibles...")

        frame_count = 0
        fragments_found = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % 50 == 0:
                print(f"  Analizando frame {frame_count + 1}/{total_frames} - Fragmentos: {fragments_found}")

            # Buscar QR codes en este frame
            qr_data_list = self.scan_frame_for_qrs(frame)

            # Procesar cada QR encontrado
            for qr_data in qr_data_list:
                fragment = self.parse_fragment(qr_data)
                if fragment:
                    idx = fragment['index']
                    if idx not in self.extracted_fragments:
                        self.extracted_fragments[idx] = fragment
                        fragments_found += 1

                        if self.total_fragments is None:
                            self.total_fragments = fragment['total']
                            print(f"📱 Total de fragmentos esperados: {self.total_fragments}")

            frame_count += 1

        cap.release()

        print(f"✅ Extracción completada")
        print(f"📱 Fragmentos encontrados: {fragments_found}")
        print(f"📱 Fragmentos esperados: {self.total_fragments}")

        return fragments_found > 0

    def reconstruct_data(self) -> Optional[bytes]:
        """
        Reconstruir datos originales desde fragmentos extraídos
        """
        if not self.extracted_fragments:
            print("❌ No hay fragmentos para reconstruir")
            return None

        if self.total_fragments is None:
            print("❌ Número total de fragmentos desconocido")
            return None

        print(f"🔧 Reconstruyendo datos desde {len(self.extracted_fragments)} fragmentos...")

        # Verificar que tenemos todos los fragmentos necesarios
        missing_fragments = []
        for i in range(self.total_fragments):
            if i not in self.extracted_fragments:
                missing_fragments.append(i)

        if missing_fragments:
            print(f"⚠️ Fragmentos faltantes: {len(missing_fragments)}")
            if len(missing_fragments) > self.total_fragments * 0.1:  # Más del 10% faltante
                print(f"❌ Demasiados fragmentos faltantes ({len(missing_fragments)}/{self.total_fragments})")
                return None
            else:
                print(f"⚠️ Continuando con {len(missing_fragments)} fragmentos faltantes...")

        # Reconstruir datos en orden
        reconstructed_data = b''
        for i in range(self.total_fragments):
            if i in self.extracted_fragments:
                reconstructed_data += self.extracted_fragments[i]['data']
            else:
                print(f"⚠️ Saltando fragmento faltante {i}")

        print(f"📦 Datos reconstruidos: {len(reconstructed_data):,} bytes")
        return reconstructed_data

    def save_reconstructed_data(self, data: bytes, output_file: str = "recovered_moby_dick.pkl.gz") -> bool:
        """
        Guardar datos reconstruidos
        """
        try:
            # Intentar descomprimir para verificar integridad
            print("🗜️ Verificando integridad de datos...")
            decompressed = gzip.decompress(data)
            recovered_dataset = pickle.loads(decompressed)

            print("✅ Datos verificados correctamente!")
            print(f"📚 Chunks recuperados: {len(recovered_dataset.get('chunks', []))}")
            print(f"🧠 Embeddings recuperados: {len(recovered_dataset.get('embeddings', []))}")
            print(f"📖 Libro: {recovered_dataset.get('book_title', 'Desconocido')}")

            # Guardar datos recuperados
            with open(output_file, 'wb') as f:
                f.write(data)

            print(f"💾 Datos guardados en: {output_file}")
            return True

        except Exception as e:
            print(f"❌ Error verificando datos: {e}")
            return False


def main():
    """
    Demo de extracción completa
    """
    import sys

    print("🕵️ SISTEMA DE EXTRACCIÓN DE VULNERABILIDAD")
    print("🎯 Recuperando Moby Dick desde video con QR invisibles")
    print("=" * 60)

    # Configuración - Aceptar argumento de línea de comandos
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = "video_with_moby_dick.mp4"  # Default

    output_file = "recovered_moby_dick.pkl.gz"

    print(f"📹 Video a analizar: {video_path}")

    # Verificar dependencias
    try:
        import pyzbar
    except ImportError:
        print("❌ pyzbar no instalado. Instalar con: pip install pyzbar")
        print("📝 En macOS también necesitas: brew install zbar")
        return

    # Crear extractor
    extractor = QRExtractor()

    # Extraer fragmentos
    if extractor.extract_from_video(video_path):

        # Reconstruir datos
        reconstructed_data = extractor.reconstruct_data()

        if reconstructed_data:
            # Guardar y verificar
            if extractor.save_reconstructed_data(reconstructed_data, output_file):
                print("\n🎉 ¡EXTRACCIÓN EXITOSA!")
                print("🚨 VULNERABILIDAD COMPLETAMENTE DEMOSTRADA:")
                print(f"📹 Video procesado: {video_path}")
                print(f"📚 Libro recuperado: {output_file}")
                print("🔍 Sistema RAG completo extraído de video")
                print("\n💡 Siguiente paso: Crear interfaz RAG para consultas")
            else:
                print("\n❌ Error en verificación de datos")
        else:
            print("\n❌ No se pudieron reconstruir los datos")
    else:
        print("\n❌ No se encontraron fragmentos en el video")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
EXTRACTOR CALIBRADO con umbrales correctos basados en debug visual
Usar los valores reales: oscuro <= 93, claro >= 162
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
import sys


class CalibratedQRExtractor:
    def __init__(self):
        """Extractor calibrado con umbrales correctos"""
        self.extracted_fragments = {}
        self.total_fragments = None

        # UMBRALES CALIBRADOS basados en debug visual
        self.dark_threshold = 93  # <= 93 para píxeles oscuros
        self.light_threshold = 162  # >= 162 para píxeles claros
        self.min_qr_pixels = 500  # Mínimo píxeles para considerar QR válido

        print(f"🎯 Extractor calibrado:")
        print(f"  🌑 Umbral oscuro: <= {self.dark_threshold}")
        print(f"  🌕 Umbral claro: >= {self.light_threshold}")

    def enhance_invisible_qr_calibrated(self, frame: np.ndarray, region: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Mejorar QR invisible usando umbrales calibrados
        """
        x, y, w, h = region

        # Extraer región
        qr_region = frame[y:y + h, x:x + w].copy()

        # Convertir a escala de grises
        gray = cv2.cvtColor(qr_region, cv2.COLOR_BGR2GRAY)

        # Aplicar umbrales calibrados
        mask_dark = gray <= self.dark_threshold
        mask_light = gray >= self.light_threshold

        # Verificar si hay suficientes píxeles de cada tipo
        dark_count = np.sum(mask_dark)
        light_count = np.sum(mask_light)

        if dark_count > self.min_qr_pixels and light_count > self.min_qr_pixels:
            # Amplificar contraste usando umbrales reales
            enhanced = qr_region.copy()
            enhanced[mask_dark] = [0, 0, 0]  # Negro puro
            enhanced[mask_light] = [255, 255, 255]  # Blanco puro

            return enhanced

        return None

    def scan_frame_calibrated(self, frame: np.ndarray, qr_size: int = 120) -> List[bytes]:
        """
        Escanear frame usando detección calibrada
        """
        found_qrs = []
        height, width = frame.shape[:2]

        # Escanear con step más pequeño para mejor cobertura
        step_size = qr_size // 3

        scan_count = 0
        detection_count = 0

        for y in range(0, height - qr_size, step_size):
            for x in range(0, width - qr_size, step_size):
                scan_count += 1

                # Intentar detectar QR en esta región
                enhanced_qr = self.enhance_invisible_qr_calibrated(frame, (x, y, qr_size, qr_size))

                if enhanced_qr is not None:
                    detection_count += 1

                    # Intentar decodificar QR
                    qr_data = self.decode_qr_from_image(enhanced_qr)
                    if qr_data:
                        found_qrs.append(qr_data)
                        print(f"    ✅ QR encontrado en ({x},{y})")

        if scan_count > 0:
            detection_rate = detection_count / scan_count * 100
            print(f"    📊 Regiones escaneadas: {scan_count}, detecciones: {detection_count} ({detection_rate:.1f}%)")

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
                try:
                    b64_data = obj.data.decode('ascii')
                    decoded_data = base64.b64decode(b64_data)
                    return decoded_data
                except Exception:
                    continue

        except Exception:
            pass

        return None

    def parse_fragment(self, fragment_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parsear fragmento extraído y verificar integridad
        """
        try:
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

    def extract_from_video_calibrated(self, video_path: str) -> bool:
        """
        Extraer QR codes usando algoritmo calibrado
        """
        print(f"🎬 Analizando video con extractor calibrado: {video_path}")

        if not os.path.exists(video_path):
            print(f"❌ Video no encontrado: {video_path}")
            return False

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        print(f"📊 Video: {total_frames} frames a {fps:.1f} FPS")
        print("🔍 Buscando QR codes con umbrales calibrados...")

        frame_count = 0
        fragments_found = 0
        total_qrs_detected = 0

        # Procesar más frames para mejor cobertura
        frame_skip = max(1, total_frames // 200)  # Procesar hasta 200 frames

        while frame_count < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % (frame_skip * 10) == 0:
                print(
                    f"  🔍 Frame {frame_count + 1}/{total_frames} - Fragmentos únicos: {len(self.extracted_fragments)}")

            # Buscar QR codes en este frame
            qr_data_list = self.scan_frame_calibrated(frame)
            total_qrs_detected += len(qr_data_list)

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
                            print(f"📱 Total fragmentos esperados: {self.total_fragments}")

            frame_count += frame_skip

        cap.release()

        print(f"\n✅ Extracción calibrada completada")
        print(f"📱 QR codes detectados: {total_qrs_detected}")
        print(f"📱 Fragmentos únicos: {len(self.extracted_fragments)}")
        print(f"📱 Fragmentos esperados: {self.total_fragments}")

        if self.total_fragments:
            completion_rate = len(self.extracted_fragments) / self.total_fragments * 100
            print(f"📊 Tasa de completitud: {completion_rate:.1f}%")

        return len(self.extracted_fragments) > 0

    def reconstruct_data(self) -> Optional[bytes]:
        """
        Reconstruir datos desde fragmentos calibrados
        """
        if not self.extracted_fragments:
            print("❌ No hay fragmentos para reconstruir")
            return None

        if self.total_fragments is None:
            print("❌ Número total de fragmentos desconocido")
            return None

        print(f"🔧 Reconstruyendo datos desde {len(self.extracted_fragments)} fragmentos...")

        # Verificar fragmentos faltantes
        missing_fragments = []
        for i in range(self.total_fragments):
            if i not in self.extracted_fragments:
                missing_fragments.append(i)

        if missing_fragments:
            print(f"⚠️ Fragmentos faltantes: {len(missing_fragments)} de {self.total_fragments}")
            if len(missing_fragments) > self.total_fragments * 0.3:  # Más del 30% faltante
                print(f"❌ Demasiados fragmentos faltantes para reconstrucción confiable")
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

    def save_reconstructed_data(self, data: bytes, output_file: str = "recovered_moby_dick_calibrated.pkl.gz") -> bool:
        """
        Guardar y verificar datos reconstruidos
        """
        try:
            print("🗜️ Verificando integridad de datos reconstruidos...")
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
    Demo de extracción calibrada
    """
    print("🎯 EXTRACTOR CALIBRADO - VULNERABILIDAD YOUTUBE")
    print("🔍 Usando umbrales basados en debug visual")
    print("=" * 60)

    # Obtener video desde argumentos o usar default
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = "video_opacity_0.120.mp4"  # Video con opacidad conocida

    output_file = "recovered_moby_dick_calibrated.pkl.gz"

    print(f"📹 Video a analizar: {video_path}")

    # Verificar dependencias
    try:
        import pyzbar
    except ImportError:
        print("❌ pyzbar no instalado. Instalar con: pip install pyzbar")
        return

    # Crear extractor calibrado
    extractor = CalibratedQRExtractor()

    # Extraer fragmentos
    if extractor.extract_from_video_calibrated(video_path):

        # Reconstruir datos
        reconstructed_data = extractor.reconstruct_data()

        if reconstructed_data:
            # Guardar y verificar
            if extractor.save_reconstructed_data(reconstructed_data, output_file):
                print("\n🎉 ¡EXTRACCIÓN CALIBRADA EXITOSA!")
                print("🚨 VULNERABILIDAD COMPLETAMENTE DEMOSTRADA:")
                print(f"📹 Video procesado: {video_path}")
                print(f"📚 Libro recuperado: {output_file}")
                print("🔍 Sistema RAG completo extraído de video")
                print("\n🎯 ¡TU INVESTIGACIÓN DE VULNERABILIDADES ESTÁ COMPLETA!")
                print("📝 Listo para crear paper y reportar a YouTube")
            else:
                print("\n❌ Error en verificación de datos")
        else:
            print("\n❌ No se pudieron reconstruir los datos")
    else:
        print("\n❌ No se encontraron fragmentos en el video")
        print("💡 Sugerencias:")
        print("  1. Usar video con mayor opacidad")
        print("  2. Verificar que el video tiene QR codes embebidos")


if __name__ == "__main__":
    main()
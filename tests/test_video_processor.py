# tests/test_video_processor.py
# (Este teste foca no serviço de processamento, independente da API/GCS)
import os
import cv2
import zipfile
import numpy as np
import pytest
from app.services.video_processor import VideoProcessor # Importa a classe
import tempfile # Usar tempfile para arquivos temporários

# Função helper para criar vídeo de teste (pode ir para conftest se usada em mais lugares)
def create_test_video(path, duration=2, fps=24, size=(320,240)):
    """Cria um arquivo de vídeo AVI para testes."""
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(str(path), fourcc, float(fps), size)
    if not out.isOpened():
        raise IOError(f"Não foi possível abrir o arquivo de vídeo para escrita: {path}")
    for i in range(int(duration * fps)):
        # Cria um frame simples (fundo branco com número do frame)
        frame = 255 * np.ones((size[1], size[0], 3), dtype=np.uint8)
        cv2.putText(frame, f"Frame {i}", (10, size[1] // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)
        out.write(frame)
    out.release()
    print(f"Vídeo de teste criado em: {path}")

def test_video_processor_success():
    # Usar diretório temporário gerenciado pelo pytest
    with tempfile.TemporaryDirectory() as tmpdir:
        video_file = os.path.join(tmpdir, "video.avi")
        output_zip = os.path.join(tmpdir, "out.zip")

        # Criar vídeo de teste (ex: 2 segundos, 10 fps)
        create_test_video(video_file, duration=2, fps=10)

        # Processar com intervalo de 1 segundo
        success = VideoProcessor.process_video(
            video_file, output_zip, time_interval=1
        )

        # Asserts
        assert success is True
        assert os.path.exists(output_zip)

        # Verificar conteúdo do ZIP
        with zipfile.ZipFile(output_zip) as zf:
            names = zf.namelist()
            # Espera-se frames em 0s e 1s (total 2) para um vídeo de 2s com intervalo de 1s
            assert len(names) == 2
            assert all(name.endswith(".jpg") for name in names)
            assert "frame_0s.jpg" in names
            assert "frame_1s.jpg" in names

def test_video_processor_invalid_input():
    processor = VideoProcessor()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_zip = os.path.join(tmpdir, "out.zip")
        with pytest.raises((ValueError, Exception)):
            processor.process_video("nonexistent_file.mp4", output_zip)

def test_video_processor_zero_interval():
    with tempfile.TemporaryDirectory() as tmpdir:
        video_file = os.path.join(tmpdir, "video.avi")
        output_zip = os.path.join(tmpdir, "out.zip")
        create_test_video(video_file, duration=1, fps=10)
        with pytest.raises(Exception):
             VideoProcessor.process_video(video_file, output_zip, time_interval=0)
import pytest
import os
import cv2
import zipfile
from app.services.video_processor import VideoProcessor

def create_test_video(filename, duration=5, fps=30, width=640, height=480):
    # Criar um vídeo de teste
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    # Criar frames com números de 1 a duration*fps
    for i in range(int(duration * fps)):
        frame = 255 * np.ones((height, width, 3), dtype=np.uint8)
        cv2.putText(frame, f'Frame {i}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        out.write(frame)
    
    out.release()

def test_video_processor():
    # Criar diretório para testes
    os.makedirs("tests/test_outputs", exist_ok=True)
    
    # Criar um vídeo de teste com duração de 5 segundos a 30 fps
    test_video = "tests/test_video.avi"
    create_test_video(test_video)
    
    # Processar o vídeo
    output_path = "tests/test_outputs/test_output.zip"
    processor = VideoProcessor()
    result = processor.process_video(test_video, output_path, time_interval=1)
    
    # Verificar se o processamento foi bem-sucedido
    assert result is True
    assert os.path.exists(output_path)
    
    # Verificar o conteúdo do zip
    with zipfile.ZipFile(output_path, 'r') as zipf:
        files = zipf.namelist()
        # Deve ter aproximadamente 5 frames (um por segundo em um vídeo de 5 segundos)
        assert len(files) >= 4
        assert len(files) <= 6
    
    # Limpar arquivos de teste
    os.remove(test_video)
    os.remove(output_path)

def test_video_processor_nonexistent_file():
    processor = VideoProcessor()
    with pytest.raises(Exception):
        processor.process_video("nonexistent_file.mp4", "output.zip")
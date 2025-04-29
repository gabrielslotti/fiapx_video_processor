# app/services/video_processor.py
import cv2
import zipfile
import os

class VideoProcessor:
    @staticmethod
    def process_video(video_path: str, output_path: str, time_interval: int = 20):
        """
        Processa o vídeo e retorna um arquivo zip com os frames
        Salva um frame a cada time_interval segundos
        """
        video_name = video_path.split("/")[-1].split(".")[0]
        print(f"Processando o vídeo {video_name}")

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            cap.release()
            raise ValueError(f"Não foi possível abrir o arquivo de vídeo: {video_path}")

        try:
            # Obter o FPS (frames por segundo) do vídeo
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"Video FPS: {fps}")
            
            # Calcular quantos frames equivalem a time_interval segundos
            frames_per_interval = int(fps * time_interval)
            print(f"Salvando um frame a cada {frames_per_interval} frames ({time_interval} segundos)")
            
            frame_count = 0
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with zipfile.ZipFile(output_path, 'w') as zipf:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    if frame_count % frames_per_interval == 0:
                        frame_path = f"/tmp/frame_{frame_count // fps:.0f}s.jpg"
                        cv2.imwrite(frame_path, frame)
                        zipf.write(frame_path, os.path.basename(frame_path))
                        os.remove(frame_path)
                    
                    frame_count += 1
            
            cap.release()
            return True
            
        except Exception as e:
            raise Exception(f"Error processing video: {str(e)}")
        finally:
            if cap.isOpened():
                cap.release()
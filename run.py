import sys
import os
import subprocess
import cv2
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
    QStyle,
    QGridLayout,
    QProgressBar,
    QMenuBar,
    QAction,
    QSlider,
)
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, QTimer

class VideoProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Frame Extraction and Summarization")
        self.setWindowIcon(QIcon.fromTheme("video-display"))
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QGridLayout()
        self.central_widget.setLayout(self.layout)

        font = QFont("Arial", 12)

        # Video Path Label and Entry
        self.label_video_path = QLabel("Enter the path to the video file:")
        self.label_video_path.setFont(font)
        self.label_video_path.setToolTip("Enter the path to the video file you want to process")
        self.layout.addWidget(self.label_video_path, 0, 0)

        self.entry_video_path = QLineEdit()
        self.entry_video_path.setFont(font)
        self.entry_video_path.setToolTip("Enter the path or click 'Choose File' to select a video file")
        self.layout.addWidget(self.entry_video_path, 0, 1)

        # Choose File Button
        self.button_choose_file = QPushButton("Choose File")
        self.button_choose_file.setFont(font)
        self.button_choose_file.setIcon(QApplication.style().standardIcon(QStyle.SP_DialogOpenButton))
        self.button_choose_file.setToolTip("Click to select a video file")
        self.button_choose_file.clicked.connect(self.choose_file)
        self.layout.addWidget(self.button_choose_file, 0, 2)

        # Extract Frames and Summarize Video Button
        self.button_extract = QPushButton("Extract Frames and Summarize Video")
        self.button_extract.setFont(font)
        self.button_extract.setStyleSheet("background-color: green; color: white")
        self.button_extract.setToolTip("Click to extract frames and summarize the video")
        self.button_extract.setIcon(QIcon.fromTheme("media-playback-start"))
        self.button_extract.clicked.connect(self.extract_frames)
        self.layout.addWidget(self.button_extract, 1, 0, 1, 3)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(font)
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar, 2, 0, 1, 3)

        # Status Label
        self.status_label = QLabel()
        self.status_label.setFont(font)
        self.layout.addWidget(self.status_label, 3, 0, 1, 3)

        # Video Display Label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.video_label, 4, 0, 1, 3)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_video_frame)
        
        # Play Button
        self.play_button = QPushButton("Play/Pause")
        self.play_button.setFont(font)
        self.play_button.setIcon(QIcon.fromTheme("media-playback-start"))
        self.play_button.clicked.connect(self.toggle_play)
        self.layout.addWidget(self.play_button, 5, 0)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setMinimum(0)
        self.seek_slider.sliderMoved.connect(self.seek_video)
        self.layout.addWidget(self.seek_slider, 5, 1, 1, 2)

        self.current_time_label = QLabel("00:00")
        self.current_time_label.setFont(font)
        self.layout.addWidget(self.current_time_label, 5, 3)

        self.timer_interval = 30
        self.playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0  # Define fps as an instance variable

        # Menu Bar
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("&File")
        open_action = QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open a video file")
        open_action.triggered.connect(self.choose_file)
        file_menu.addAction(open_action)

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def choose_file(self):
        video_file, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", "Video files (*.mp4 *.avi *.mkv)"
        )
        if video_file:
            self.entry_video_path.setText(video_file)

    def extract_frames(self):
        video_path = self.entry_video_path.text().strip()
        if not video_path:
            self.show_error_message("Please enter the video path!")
            return

        if not os.path.isfile(video_path):
            self.show_error_message("Video file does not exist!")
            return

        videoframe_directory = os.path.join(os.path.dirname(video_path), "videoframes")
        os.makedirs(videoframe_directory, exist_ok=True)

        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("Extracting frames...")

            subprocess.run(
                ["python", "Cricket_Videoframes/videoframes.py", video_path, videoframe_directory],
                check=True,
            )
            self.progress_bar.setValue(50)
            self.status_label.setText("Frames extraction completed.")

            subprocess.run(
                [
                    "python",
                    "summary2video.py",
                    "-p",
                    "log/summe-split0/result.h5",
                    "-d",
                    videoframe_directory,
                    "-i",
                    "0",
                    "--fps",
                    "60",
                    "--save-dir",
                    "log",
                    "--save-name",
                    "summary1.mp4",
                ],
                check=True,
            )
            self.progress_bar.setValue(100)
            self.status_label.setText("Video summarization completed.")
            self.progress_bar.setVisible(False)

            summarized_video = os.path.join("log", "summary1.mp4")
            if os.path.isfile(summarized_video):
                self.play_video(summarized_video)
        except subprocess.CalledProcessError as e:
            self.show_error_message(f"Error occurred: {e}")

    def play_video(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))  # Assign fps

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_video_frame)
        self.timer.start(self.timer_interval)  # Update every 30 milliseconds

    def toggle_play(self):
        if self.playing:
            self.timer.stop()
            self.play_button.setIcon(QIcon.fromTheme("media-playback-start"))
        else:
            self.timer.start(self.timer_interval)
            self.play_button.setIcon(QIcon.fromTheme("media-playback-pause"))
        self.playing = not self.playing

    def seek_video(self, value):
        target_frame = int(value / 100 * self.total_frames)  # Use self.total_frames
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        self.current_frame = target_frame

    def update_video_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.release()
            self.timer.stop()
            return

        self.current_frame += 1
        self.seek_slider.setValue(int(self.current_frame / self.total_frames * 100))  # Use self.total_frames

        if self.current_frame >= self.total_frames:
            self.cap.release()
            self.timer.stop()
            self.play_button.setIcon(QIcon.fromTheme("media-playback-start"))
            self.playing = False
            return

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        qimage = QImage(rgb_frame, rgb_frame.shape[1], rgb_frame.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        pixmap = pixmap.scaled(640, 480, Qt.KeepAspectRatio)

        self.video_label.setPixmap(pixmap)
        self.video_label.adjustSize()

        current_time = int(self.current_frame / self.fps)
        minutes = current_time // 60
        seconds = current_time % 60
        self.current_time_label.setText(f"{minutes:02}:{seconds:02}")

    def show_error_message(self, message):
        QMessageBox.warning(self, "Error", message)

def main():
    app = QApplication(sys.argv)
    window = VideoProcessorApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
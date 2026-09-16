from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtCore import QObject, QUrl

class AudioPlayer(QObject):
    def __init__(self):
        super().__init__()

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()

        self.player.setAudioOutput(self.audio_output)

    def play_file(self, file_path):
        self.player.stop()
        self.player.setSource(file_path)
        self.player.play()

    def stop(self):
        self.player.stop()

    def release_source(self):
        self.player.stop()
        self.player.setSource(QUrl())

    def toggle_playback(self):
        state = self.player.playbackState()

        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()

        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()

        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.player.setPosition(0)
            self.player.play()

    def seek(self, position):
        self.player.setPosition(position)
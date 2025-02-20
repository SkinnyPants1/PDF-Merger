import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                             QFileDialog, QMessageBox, QProgressBar, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
                             QScrollArea)
from PyPDF2 import PdfMerger
from PyQt5.QtCore import pyqtSignal, QThread, Qt
import os
import qdarktheme
import fitz
from PyQt5.QtGui import QPixmap, QImage

class PdfMergeThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, files, target_file):
        super().__init__()
        self.files = files
        self.target_file = target_file

    def run(self):
        try:
            merger = PdfMerger()
            for file in self.files:
                merger.append(file)
            merger.write(self.target_file)
            merger.close()
            self.finished.emit("Udah digabung semua yak.")
        except Exception as e:
            self.finished.emit(f"Ada yang salah brok: {str(e)}")

class PdfMergerApp(QWidget):
    def __init__(self):
        super().__init__()

        # Inisialisasi komponen UI
        self.add_file_button = QPushButton("Pilih File PDF")
        self.file_list_widget = QListWidget()
        self.file_paths = []

        # Label
        self.label3 = QLabel("Lokasi Penyimpanan:")
        self.button3 = QPushButton("Pilih")
        self.merge_button = QPushButton("Gabungkan")
        self.progress_bar = QProgressBar()
        self.label_filename = QLabel("Nama File:")
        self.filename_input = QLineEdit()
        self.ulang = QPushButton("Restart")

        # Layout
        main_layout = QHBoxLayout()  # Layout utama menjadi horizontal

        # Layout sebelah kiri untuk kontrol
        left_layout = QVBoxLayout()

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.add_file_button)
        hbox2.addWidget(self.ulang)
        left_layout.addLayout(hbox2)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.label3)
        hbox3.addWidget(self.button3)
        left_layout.addLayout(hbox3)

        filename_layout = QHBoxLayout()
        filename_layout.addWidget(self.label_filename)
        filename_layout.addWidget(self.filename_input)
        left_layout.addLayout(filename_layout)

        left_layout.addWidget(self.merge_button)
        left_layout.addWidget(self.file_list_widget)
        left_layout.addWidget(self.progress_bar)

        main_layout.addLayout(left_layout)

        # Layout sebelah kanan untuk preview
        right_layout = QVBoxLayout()

        # Tambahkan QScrollArea untuk preview
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        right_layout.addWidget(self.scroll_area)

        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

        # Mengaktifkan drag-and-drop
        self.file_list_widget.setDragEnabled(True)
        self.file_list_widget.setAcceptDrops(True)
        self.file_list_widget.setDropIndicatorShown(True)
        self.file_list_widget.setDragDropMode(QListWidget.InternalMove)

        # Koneksi sinyal dan slot
        self.add_file_button.clicked.connect(self.add_file)
        self.button3.clicked.connect(self.choose_target)
        self.merge_button.clicked.connect(self.merge_pdf)
        self.ulang.clicked.connect(self.hapus)
        self.file_list_widget.model().rowsMoved.connect(self.update_file_paths)
        self.file_list_widget.itemDoubleClicked.connect(self.remove_file)

        self.target_path = ""

    def add_file(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("PDF files (*.pdf)")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            self.add_file_button.setText("Tambah File PDF")
            for file in selected_files:
                self.file_paths.append(file)
                item = QListWidgetItem(os.path.basename(file))
                item.setData(1, file)
                self.file_list_widget.addItem(item)
            self.update_preview()

    def remove_file(self, item):
        row = self.file_list_widget.row(item)
        if row >= 0:
            self.file_list_widget.takeItem(row)
            self.file_paths.pop(row)
            self.update_preview()

    def choose_target(self):
        folder_dialog = QFileDialog()
        folder_dialog.setFileMode(QFileDialog.DirectoryOnly)
        if folder_dialog.exec_():
            self.target_path = folder_dialog.selectedFiles()[0]
            self.button3.setText(self.target_path)

    def merge_pdf(self):
        filename = self.filename_input.text()
        if not filename:
            QMessageBox.warning(self, "WOY WOY WOY!",
                                "Kasih nama filenya dulu dong bang.")
            return

        if not self.file_paths:
            QMessageBox.warning(self, "WOOOOYYYY!",
                                "Yakali apa yang mau digabungin bang?")
            return

        if len(self.file_paths) < 2:
            QMessageBox.warning(self, "WOOOOYYYY!",
                                "Yakali cuma satu doang bang filenya.")
            return

        self.target_file = os.path.join(self.target_path, filename + ".pdf")

        self.progress_bar.setValue(0)
        self.thread = PdfMergeThread(self.file_paths, self.target_file)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def hapus(self):
        self.file_list_widget.clear()
        self.file_paths.clear()
        self.update_preview()

    def on_finished(self, message):
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Done!", message)

        self.hapus()
        self.add_file_button.setText("Pilih File PDF")
        self.button3.setText("Pilih")
        self.filename_input.clear()
        self.progress_bar.setValue(0)

    def update_file_paths(self):
        new_order = []
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            new_order.append(item.data(1))
        self.file_paths = new_order
        self.update_preview()

    def update_preview(self):
        # Hapus semua preview yang ada
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)

        if not self.file_paths:
            return

        try:
            for file_idx, file_path in enumerate(self.file_paths, start=1):
                doc = fitz.open(file_path)
                for page_idx, page in enumerate(doc, start=1):
                    pix = page.get_pixmap()
                    img = QImage(pix.samples, pix.width, pix.height,
                                 pix.stride, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(img)

                    # Tambahkan label untuk nama file dan nomor halaman
                    label_filename = QLabel(
                        f"File {file_idx}: {os.path.basename(file_path)} - Halaman {page_idx}"
                    )
                    self.scroll_layout.addWidget(label_filename)

                    label = QLabel()
                    label.setPixmap(pixmap)
                    self.scroll_layout.addWidget(label)

        except Exception as e:
            print(f"Error saat menampilkan preview: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    window = PdfMergerApp()
    window.setWindowTitle("Alat Penggabung PDF!")
    window.show()
    sys.exit(app.exec_())

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QFileDialog, QMessageBox, QProgressBar, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from PyPDF2 import PdfMerger  # Pastikan Anda menggunakan PdfMerger dari PyPDF2
from PyQt5.QtCore import pyqtSignal, QThread
import os
import qdarktheme

class PdfMergeThread(QThread):
    finished = pyqtSignal(str)  # Emit string untuk pesan hasil

    def __init__(self, files, target_file):
        super().__init__()
        self.files = files
        self.target_file = target_file

    def run(self):
        try:
            merger = PdfMerger()  # Buat instance PdfMerger
            for file in self.files:
                merger.append(file)  # Tambahkan setiap file PDF
            merger.write(self.target_file)  # Tulis ke file target
            merger.close()  # Tutup merger
            self.finished.emit("Udah digabung semua yak.")
        except Exception as e:
            self.finished.emit(f"Ada yang salah brok: {str(e)}")

class PdfMergerApp(QWidget):
    def __init__(self):
        super().__init__()

        # Inisialisasi komponen UI
        self.add_file_button = QPushButton("Pilih File PDF")
        self.file_list_widget = QListWidget()  # Ganti QLabel dengan QListWidget
        self.file_paths = []  # List untuk menyimpan path file

        # Label
        self.label3 = QLabel("Lokasi Penyimpanan:")
        self.button3 = QPushButton("Pilih")
        self.merge_button = QPushButton("Gabungkan")
        self.progress_bar = QProgressBar()
        self.label_filename = QLabel("Nama File:")
        self.filename_input = QLineEdit()
        self.ulang = QPushButton("Restart")

        # Baris 1
        layout = QVBoxLayout()
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.add_file_button) # Tambahkan button "Pilih File PDF" ke layout
        hbox2.addWidget(self.ulang) # Tambahkan button "Restart" ke layout
        layout.addLayout(hbox2)

        # Baris 2
        hbox3 = QHBoxLayout()
        hbox3.addWidget(self.label3) # Tambahkan label "Lokasi Penyimpanan:" ke layout
        hbox3.addWidget(self.button3) # Tambahkan button "Pilih" ke layout
        layout.addLayout(hbox3)

        # Baris 3
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(self.label_filename) # Tambahkan label "Nama File:" ke layout
        filename_layout.addWidget(self.filename_input) # Tambahkan input nama file ke layout
        layout.addLayout(filename_layout)

        # Baris 4
        layout.addWidget(self.merge_button) # Tambahkan button "Gabungkan" ke layout

        # Baris 5
        layout.addWidget(self.file_list_widget)  # Box layout untuk menampilkan file yang dipilih

        # Baris 6
        layout.addWidget(self.progress_bar) # Tambahkan progress bar ke layout

        self.setLayout(layout)

        # Koneksi sinyal dan slot
        self.add_file_button.clicked.connect(self.add_file) # Koneksi button "Pilih File PDF" ke slot "add_file"
        self.button3.clicked.connect(self.choose_target) # Koneksi button "Pilih" ke slot "choose_target"
        self.merge_button.clicked.connect(self.merge_pdf) # Koneksi button "Gabungkan" ke slot "merge_pdf"
        self.ulang.clicked.connect(self.hapus) # Koneksi button "Restart" ke slot "hapus"

        self.target_path = ""

    def add_file(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("PDF files (*.pdf)")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)  # Allow multiple file selection
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            self.add_file_button.setText("Tambah File PDF")
            for file in selected_files:
                self.file_paths.append(file)
                self.create_file_row(file)  # Create a row for the selected file

    def create_file_row(self, file):
        item = QListWidgetItem(os.path.basename(file))  # Create a list item for the file name
        item.setData(1, file)  # Store the full path in the item data
        self.file_list_widget.addItem(item)  # Add item to QListWidget

        # Add a deletebutton to remove the file from the list
        delete_button = QPushButton("                                                               Hapus")
        delete_button.clicked.connect(lambda: self.remove_file(item))
        self.file_list_widget.setItemWidget(item, delete_button)  # Set the delete button as the widget for the item

    def remove_file(self, item):
        row = self.file_list_widget.row(item)  # Get the row of the item
        self.file_list_widget.takeItem(row)  # Remove the item from the list
        self.file_paths.pop(row)  # Remove the corresponding file path from the list

    def choose_target(self):
        folder_dialog = QFileDialog()
        folder_dialog.setFileMode(QFileDialog.DirectoryOnly)
        if folder_dialog.exec_():
            self.target_path = folder_dialog.selectedFiles()[0]
            self.button3.setText(self.target_path)

    def merge_pdf(self):
        filename = self.filename_input.text()
        if not filename:
            QMessageBox.warning(self, "WOY WOY WOY!", "Kasih nama filenya dulu dong bang.")
            return

        if not self.file_paths:
            QMessageBox.warning(self, "WOOOOYYYY!", "Yakali apa yang mau digabungin bang?")
            return
        
        if len(self.file_paths) < 2:
            QMessageBox.warning(self, "WOOOOYYYY!", "Yakali cuma satu doang bang filenya.")
            return

        self.target_file = os.path.join(self.target_path, filename + ".pdf")

        self.progress_bar.setValue(0)
        self.thread = PdfMergeThread(self.file_paths, self.target_file)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def hapus(self):
        self.file_list_widget.clear()  # Menghapus semua item dari QListWidget
        self.file_paths.clear()  # Reset list path file

    def on_finished(self, message):
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Done!", message)

        self.hapus()  # Menghapus semua item dari QListWidget
        self.add_file_button.setText("Pilih File PDF")  # Reset tombol tambah file
        self.button3.setText("Pilih")  # Reset tombol lokasi penyimpanan
        self.filename_input.clear()  # Kosongkan input nama file
        self.progress_bar.setValue(0)  # Reset progress bar

if __name__ == '__main__':
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    window = PdfMergerApp()
    window.setWindowTitle("Alat Penggabung PDF!")  # judul software
    window.setFixedSize(800,700)
    window.show()
    sys.exit(app.exec_())

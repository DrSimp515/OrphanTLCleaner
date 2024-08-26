import os
import re
import sys
from PyQt5.QtCore import QTranslator, QCoreApplication, QLocale, QSettings
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTextEdit, QLabel, QLineEdit, QComboBox, QCheckBox
from PyQt5.QtGui import QIcon

class OrphanTLCleaner(QWidget):
    def __init__(self):
        super().__init__()
        self.translator = QTranslator()
        self.settings = QSettings('MyApp', 'OrphanTLCleaner')

        self.init_ui()

        saved_locale = self.settings.value('locale', QLocale.system().name())
        self.set_language(saved_locale)

        saved_theme = self.settings.value('theme', 'light')
        self.set_theme(saved_theme)

    def init_ui(self):
        self.setWindowTitle(self.tr('Limpiador de TLs Huérfanas'))
        self.setGeometry(100, 100, 600, 500)

        icon_path = os.path.join(os.path.abspath("."), "icon.ico")
        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "icon.ico")

        self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()

        self.language_selector = QComboBox(self)
        self.language_selector.addItem("Español", "es_ES")
        self.language_selector.addItem("English", "en_US")
        self.language_selector.addItem("Français", "fr_FR")
        self.language_selector.addItem("Português (Brasil)", "pt_BR")
        self.language_selector.addItem("日本語", "ja_JP")
        self.language_selector.addItem("Русский", "ru_RU")
        self.language_selector.addItem("中文（繁體）", "zh_TW")

        self.language_selector.currentIndexChanged.connect(self.change_language)
        layout.addWidget(self.language_selector)

        self.dark_mode_checkbox = QCheckBox(self.tr("Modo oscuro"))
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_mode_checkbox)

        self.comment_blocks_checkbox = QCheckBox(self.tr("Comentar bloques en lugar de borrarlos"))
        self.comment_blocks_checkbox.setChecked(False)
        layout.addWidget(self.comment_blocks_checkbox)

        self.directory_label = QLabel(self.tr("Seleccione el directorio con los archivos .rpy y .rpym"))
        layout.addWidget(self.directory_label)

        self.select_directory_button = QPushButton(self.tr('Seleccionar Directorio'))
        self.select_directory_button.clicked.connect(self.select_directory)
        layout.addWidget(self.select_directory_button)

        self.lint_file_label = QLabel(self.tr("Seleccione el archivo lint.txt"))
        layout.addWidget(self.lint_file_label)

        self.select_lint_button = QPushButton(self.tr('Seleccionar lint.txt'))
        self.select_lint_button.clicked.connect(self.select_lint_file)
        layout.addWidget(self.select_lint_button)

        self.language_label = QLabel(self.tr("Ingrese el idioma a buscar (por ejemplo, 'english')"))
        layout.addWidget(self.language_label)

        self.language_input = QLineEdit()
        layout.addWidget(self.language_input)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        self.run_button = QPushButton(self.tr('Ejecutar'))
        self.run_button.clicked.connect(self.run_tool)
        layout.addWidget(self.run_button)

        self.setLayout(layout)

        self.directory = None
        self.lint_file = None

    def set_language(self, locale):
        index = self.language_selector.findData(locale)
        if index != -1:
            self.language_selector.setCurrentIndex(index)

        self.load_translation(locale)

    def change_language(self):
        locale = self.language_selector.currentData()

        self.settings.setValue('locale', locale)

        self.load_translation(locale)

    def load_translation(self, locale):
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        translation_file = os.path.join(base_path, 'languages', f'{locale}.qm')

        if self.translator.load(translation_file):
            app.installTranslator(self.translator)
        else:
            app.removeTranslator(self.translator)

        self.update_ui_texts()

    def update_ui_texts(self):
        self.setWindowTitle(self.tr('Limpiador de TLs Huérfanas'))
        self.dark_mode_checkbox.setText(self.tr("Modo oscuro"))
        self.comment_blocks_checkbox.setText(self.tr("Comentar bloques en lugar de borrarlos"))
        self.directory_label.setText(self.tr("Seleccione el directorio con los archivos .rpy y .rpym"))
        self.select_directory_button.setText(self.tr('Seleccionar Directorio'))
        self.lint_file_label.setText(self.tr("Seleccione el archivo lint.txt"))
        self.select_lint_button.setText(self.tr('Seleccionar lint.txt'))
        self.language_label.setText(self.tr("Ingrese el idioma a buscar (por ejemplo, 'english')"))
        self.run_button.setText(self.tr('Ejecutar'))

    def select_directory(self):
        self.directory = QFileDialog.getExistingDirectory(self, self.tr('Seleccione Directorio'))
        if self.directory:
            self.directory_label.setText(self.tr(f"Directorio seleccionado: {self.directory}"))

    def select_lint_file(self):
        self.lint_file, _ = QFileDialog.getOpenFileName(self, self.tr('Seleccione lint.txt'), '', self.tr('Text Files (*.txt)'))
        if self.lint_file:
            self.lint_file_label.setText(self.tr(f"lint.txt seleccionado: {self.lint_file}"))

    def run_tool(self):
        if not self.directory or not self.lint_file:
            self.result_text.setText(self.tr("Seleccione el directorio y el archivo lint.txt primero."))
            return

        language = self.language_input.text().strip()
        if not language:
            self.result_text.setText(self.tr("Por favor, ingrese un idioma."))
            return

        identifiers = self.load_identifiers(self.lint_file)
        if not identifiers:
            self.result_text.setText(self.tr("No se encontraron identificadores en lint.txt."))
            return

        files_processed = []
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith('.rpy') or file.endswith('.rpym'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    updated_content = self.process_file(content, identifiers, language)

                    if updated_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        files_processed.append(filepath)

        self.result_text.setText(self.tr("Archivos procesados:\n") + "\n".join(files_processed))

    def load_identifiers(self, lint_file):
        with open(lint_file, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = r'\(id (\w+)\)'
        matches = re.findall(pattern, content)

        return matches

    def process_file(self, content, identifiers, language):
        for identifier in identifiers:
            pattern = rf'(?m)^translate\s+{re.escape(language)}\s+{re.escape(identifier)}:(.*?)^(?=\S|\Z)'
            compiled_pattern = re.compile(pattern, re.DOTALL)
            bloque_match = compiled_pattern.search(content)
            if bloque_match:
                bloque_completo = bloque_match.group(0)
                if self.comment_blocks_checkbox.isChecked():
                    lineas_bloque = bloque_completo.strip().split("\n")
                    lineas_modificadas = ["# " + linea if linea.strip() else "" for linea in lineas_bloque]
                    bloque_modificado = "\n".join(lineas_modificadas) + "\n\n"
                else:
                    bloque_modificado = ""

                content = content.replace(bloque_completo, bloque_modificado)

        return content

    def toggle_dark_mode(self, state):
        if state == 2:
            self.setStyleSheet("QWidget { background-color: #2b2b2b; color: #f0f0f0; }"
                               "QLineEdit { background-color: #3c3c3c; color: #f0f0f0; }"
                               "QTextEdit { background-color: #3c3c3c; color: #f0f0f0; }"
                               "QPushButton { background-color: #4c4c4c; color: #f0f0f0; }"
                               "QComboBox { background-color: #3c3c3c; color: #f0f0f0; }")
            self.settings.setValue('theme', 'dark')
        else:
            self.setStyleSheet("")
            self.settings.setValue('theme', 'light')

    def set_theme(self, theme):
        if theme == 'dark':
            self.dark_mode_checkbox.setChecked(True)
            self.toggle_dark_mode(2)
        else:
            self.dark_mode_checkbox.setChecked(False)
            self.toggle_dark_mode(0)

if __name__ == '__main__':
    app = QApplication([])

    tool = OrphanTLCleaner()
    tool.show()
    app.exec_()

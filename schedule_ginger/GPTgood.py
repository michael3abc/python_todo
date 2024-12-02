from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
                               QStackedWidget, QTableWidget, QTableWidgetItem, QSizePolicy, QTimeEdit, QSpinBox, 
                               QLineEdit, QFrame, QDialog, QScrollArea, QFormLayout, QDialogButtonBox, QComboBox,
                               )
from PySide6.QtCore import Qt, QTime, QMimeData
from PySide6.QtGui import QDrag, QColor
from datetime import datetime, timedelta
import csv
import sys

tagset_filelocation = 'tagset_datas.csv'
# Draggable button class
class DraggableButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.course_name = text
        self.setMouseTracking(True)
        self.setAcceptDrops(False)
        self.setMinimumHeight(30)
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.course_name)
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction | Qt.MoveAction)

# Course button widget
class CourseButtonWidget(QWidget):
    def __init__(self, course_name, delete_callback, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.course_button = DraggableButton(course_name)
        delete_button = QPushButton("×")
        delete_button.setFixedSize(20, 20)
        delete_button.clicked.connect(lambda: delete_callback(self))
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        """)

        layout.addWidget(self.course_button)
        layout.addWidget(delete_button)

# Schedule widget
class ScheduleWidget(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Weekly schedule table
        self.schedule_table = QTableWidget()
        self.schedule_table.setAcceptDrops(True)
        self.schedule_table.dragEnterEvent = self.table_drag_enter
        self.schedule_table.dragMoveEvent = self.table_drag_move
        self.schedule_table.dropEvent = self.table_drop
        self.schedule_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        main_layout.addWidget(self.schedule_table)

        self.setup_table()

    def table_drag_enter(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def table_drag_move(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def table_drop(self, event):
        pos = event.pos()
        row = self.schedule_table.rowAt(pos.y())
        col = self.schedule_table.columnAt(pos.x())
        if row >= 0 and col >= 0:
            if event.mimeData().hasText():
                course_name = event.mimeData().text()
                new_item = QTableWidgetItem(course_name)
                self.schedule_table.setItem(row, col, new_item)
                event.acceptProposedAction()

    def setup_table(self, interval_minutes=30, start_time_str="08:00", end_time_str="17:00"):
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        self.schedule_table.setColumnCount(len(weekdays))
        self.schedule_table.setHorizontalHeaderLabels(weekdays)

        # Calculate the available width for the columns
        table_width = self.schedule_table.width()/2
        column_width = table_width // len(weekdays)  # Evenly distribute the width

        # Set the column width for each column
        for col in range(len(weekdays)):
            self.schedule_table.setColumnWidth(col, column_width)

        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = datetime.strptime(end_time_str, "%H:%M")
        total_intervals = int((end_time - start_time).total_seconds() / (interval_minutes * 60)) + 1

        self.schedule_table.setRowCount(total_intervals)
        time_labels = []
        current_time = start_time
        for i in range(total_intervals):
            time_str = current_time.strftime("%H:%M")
            time_labels.append(time_str)
            current_time += timedelta(minutes=interval_minutes)

        self.schedule_table.setVerticalHeaderLabels(time_labels)

        # Adjust the height of the rows (time column)
        self.schedule_table.verticalHeader().setDefaultSectionSize(30)  # Set the default row height



# Main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule Manager")
        self.resize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Weekly schedule
        self.schedule_widget = ScheduleWidget()
        main_layout.addWidget(self.schedule_widget, stretch=1)

        # Right side navigation
        right_side = QWidget()
        right_layout = QVBoxLayout(right_side)

        button_layout = QHBoxLayout()
        self.tags_button = QPushButton("Tags")
        self.tasks_button = QPushButton("Tasks")
        self.optimize_button = QPushButton("Optimize")
        self.setting_button = QPushButton("Setting")
        button_layout.addWidget(self.tags_button)
        button_layout.addWidget(self.tasks_button)
        button_layout.addWidget(self.optimize_button)
        button_layout.addWidget(self.setting_button)

        self.page_stack = QStackedWidget()
        self.page_stack.addWidget(self.create_tags_page())
        self.page_stack.addWidget(self.create_tasks_page())
        self.page_stack.addWidget(self.create_page("Optimize Page"))
        self.settings_page = self.create_settings_page()
        self.page_stack.addWidget(self.settings_page)

        right_layout.addLayout(button_layout)
        right_layout.addWidget(self.page_stack)
        main_layout.addWidget(right_side, stretch=1)

        # Button connections
        self.tags_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(0))
        self.tasks_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(1))
        self.optimize_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(2))
        self.setting_button.clicked.connect(lambda: self.page_stack.setCurrentIndex(3))
        

    def create_tags_page(self):
        tags_page = QWidget()
        tags_layout = QVBoxLayout(tags_page)

        # Create a table to display data
        self.tags_table = QTableWidget()
        self.load_tags_data()
        tags_layout.addWidget(self.tags_table)

        # Add "Add" and "Save" buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add")
        save_button = QPushButton("Save")
        
        add_button.clicked.connect(self.add_tag_row)
        save_button.clicked.connect(self.save_tags_data)
        button_layout.addWidget(add_button)
        button_layout.addWidget(save_button)
        tags_layout.addLayout(button_layout)

        return tags_page

    def load_tags_data(self):
        """Load tags data from the CSV and display it in the table, row by row, cell by cell."""
        with open(tagset_filelocation, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=',')  # Specify the delimiter as backslash

            # Read and set the header first
            headers = next(reader)  # Get the header row
            self.tags_table.setColumnCount(len(headers) + 1)  # +1 for the delete button column
            self.tags_table.setHorizontalHeaderLabels(headers + ["Delete"])  # Add "Delete" to header

            # Read each row one by one and add each cell to the table
            row = 0
            for row_data in reader:
                self.tags_table.insertRow(row)

                # Insert the data into the respective cells
                for column, data in enumerate(row_data):
                    item = QTableWidgetItem(data)
                    self.tags_table.setItem(row, column, item)

                # Add a delete button to the last column for each row
                delete_button = QPushButton("Delete")
                delete_button.clicked.connect(lambda checked, row=row: self.delete_row(row))
                self.tags_table.setCellWidget(row, len(row_data), delete_button)

                row += 1

            # Evenly distribute the column width (including the delete column)
            self.evenly_distribute_column_widths()

    def evenly_distribute_column_widths(self):
        """Distribute the column widths evenly across the table."""
        total_width = self.tags_table.viewport().width()
        column_count = self.tags_table.columnCount()

        if column_count > 0:
            # Calculate the width for each column
            column_width = total_width/2 // column_count

            for col in range(column_count):
                self.tags_table.setColumnWidth(col, column_width)


    def add_tag_row(self):
        """Add a new row to the tags table."""
        row_position = self.tags_table.rowCount()
        self.tags_table.insertRow(row_position)

        # Add input fields for each column in the row, except the "Delete" column
        for column in range(self.tags_table.columnCount() - 1):  # Exclude the delete button column
            if column == 1:  # Assuming "Type" is at index 2
                # Create a combo box for "Type" column
                type_combo = QComboBox()
                type_combo.addItems(["int", "float", "str", "list", "dict", "bool", "set"])
                type_combo.setStyleSheet("QComboBox { text-align: left; }")  # Set text alignment to left
                self.tags_table.setCellWidget(row_position, column, type_combo)
            elif column == 3:  # Assuming "Visibility" is at index 3
                # Create a combo box for "Visibility" column
                visibility_combo = QComboBox()
                visibility_combo.addItems(["True", "False"])
                visibility_combo.setStyleSheet("QComboBox { text-align: left; }")  # Set text alignment to left
                self.tags_table.setCellWidget(row_position, column, visibility_combo)
            else:
                # For other columns, use QLineEdit
                input_field = QLineEdit()
                input_field.setAlignment(Qt.AlignLeft)  # Align text to the left
                self.tags_table.setCellWidget(row_position, column, input_field)

        # Add delete button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda checked, row=row_position: self.delete_row(row))
        self.tags_table.setCellWidget(row_position, self.tags_table.columnCount() - 1, delete_button)

    def delete_row(self, row):
        """Delete the row from the table."""
        self.tags_table.removeRow(row)

    def save_tags_data(self):
        """Save the tags data to a CSV file, excluding the last column (delete button)."""
        with open(tagset_filelocation, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Get the header from the table
            headers = []
            for column in range(self.tags_table.columnCount() - 1):  # Exclude the last column
                headers.append(self.tags_table.horizontalHeaderItem(column).text())
            writer.writerow(headers)  # Write the header row

            # Write the data rows, excluding the last column
            for row in range(self.tags_table.rowCount()):
                row_data = []
                for column in range(self.tags_table.columnCount() - 1):  # Exclude the last column
                    item = self.tags_table.item(row, column)
                    if item:  # If there's a valid item in the cell
                        row_data.append(item.text())
                    else:
                        # If the item is None, check for QLineEdit or QComboBox
                        widget = self.tags_table.cellWidget(row, column)
                        if isinstance(widget, QLineEdit):
                            row_data.append(widget.text())
                        elif isinstance(widget, QComboBox):
                            row_data.append(widget.currentText())  # For QComboBox, get the current selected text
                        else:
                            row_data.append("")  # In case of other widget types, append an empty string
                writer.writerow(row_data)  # Write the data row

                # Optionally, save the background color of the last added row or item
                # This step ensures that when the tags are loaded again, the background color is the same
                if row == self.tags_table.rowCount() - 1:  # Last row
                    for column in range(self.tags_table.columnCount() - 1):  # Exclude delete column
                        item = self.tags_table.item(row, column)
                        if item:
                            # Save the color of the item
                            saved_color = item.background()
                            self.last_row_colors = []  # Reset colors for the current row
                            self.last_row_colors.append(saved_color)



    def create_tasks_page(self):
        """
        創建 Tasks Page，並包含右下角的 "Add Task" 按鈕
        """
        tasks_page = QWidget()
        tasks_layout = QVBoxLayout(tasks_page)

        # 滾動區域，用於展示任務
        self.task_scroll_area = QScrollArea()
        self.task_scroll_area.setWidgetResizable(True)
        self.task_scroll_content = QWidget()
        self.task_scroll_layout = QVBoxLayout(self.task_scroll_content)
        self.task_scroll_area.setWidget(self.task_scroll_content)

        # 添加滾動區域到任務頁面佈局
        tasks_layout.addWidget(self.task_scroll_area)

        # "Add Task" 按鈕
        add_task_button = QPushButton("Add Task")
        add_task_button.setStyleSheet("background-color: lightgray; font-size: 14px;")
        add_task_button.clicked.connect(self.open_task_dialog)

        # 添加滾動區域和按鈕到主佈局
        tasks_layout.addWidget(add_task_button, alignment=Qt.AlignmentFlag.AlignTop)

        return tasks_page

    def create_page(self, text):
        """
        創建其他簡單的頁面
        :param text: 頁面顯示的文字
        :return: QWidget 物件
        """
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 20px;")
        layout.addWidget(label)
        return page

    def open_task_dialog(self):
        """
        打開新的對話框，讓用戶輸入任務內容
        """
        dialog = TaskDialog(self)
        if dialog.exec():  # 如果用戶按下了對話框中的 "OK"
            task_name = dialog.task_name_input.text()
            self.add_task(task_name)

    def add_task(self, task_name):
        """
        在 Tasks Page 中新增一個任務，並包含 "Edit" 和 "Delete" 按鈕
        :param task_name: 任務的名稱
        """
        task_frame = QFrame()
        task_frame.setStyleSheet("background-color: lightblue; border: 1px solid gray;")
        task_frame.setFixedHeight(50)

        task_layout = QHBoxLayout(task_frame)

        # 左側任務名稱
        task_label = QLabel(task_name)
        task_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        task_layout.addWidget(task_label, stretch=3)

        # 右側按鈕
        edit_button = QPushButton("Edit")
        delete_button = QPushButton("Delete")
        task_layout.addWidget(edit_button, stretch=1)
        task_layout.addWidget(delete_button, stretch=1)

        # ** 將新任務插入到佈局最頂部 **
        self.task_scroll_layout.insertWidget(0, task_frame)
        self.task_scroll_content.updateGeometry()

        # 連接按鈕功能
        edit_button.clicked.connect(lambda: self.edit_task(task_label))
        delete_button.clicked.connect(lambda: self.delete_task(task_frame))

    def edit_task(self, task_label):
        """
        編輯任務名稱
        :param task_label: 要編輯的任務標籤
        """
        dialog = TaskDialog(self, initial_value=task_label.text())
        if dialog.exec():  # 如果用戶按下了 "OK"
            task_label.setText(dialog.task_name_input.text())

    def delete_task(self, task_frame):
        """
        刪除任務
        :param task_frame: 要刪除的任務框架
        """
        self.task_scroll_layout.removeWidget(task_frame)
        task_frame.deleteLater()
        self.task_scroll_content.adjustSize()

    def create_settings_page(self):
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)

        time_settings = QWidget()
        time_layout = QVBoxLayout(time_settings)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(15)

        start_time_container = QWidget()
        start_time_layout = QHBoxLayout(start_time_container)
        start_time_layout.setContentsMargins(0, 0, 0, 0)
        start_time_label = QLabel("開始時間:")
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setTime(QTime(8, 0))
        start_time_layout.addWidget(start_time_label)
        start_time_layout.addWidget(self.start_time_edit)

        end_time_container = QWidget()
        end_time_layout = QHBoxLayout(end_time_container)
        end_time_layout.setContentsMargins(0, 0, 0, 0)
        end_time_label = QLabel("結束時間:")
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setTime(QTime(17, 0))
        end_time_layout.addWidget(end_time_label)
        end_time_layout.addWidget(self.end_time_edit)

        interval_container = QWidget()
        interval_layout = QHBoxLayout(interval_container)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_label = QLabel("時間間隔(分鐘):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(5, 60)
        self.interval_spinbox.setValue(30)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)

        update_button = QPushButton("更新課表")
        update_button.clicked.connect(self.update_schedule)

        time_layout.addWidget(start_time_container)
        time_layout.addWidget(end_time_container)
        time_layout.addWidget(interval_container)
        time_layout.addWidget(update_button)

        settings_layout.addWidget(time_settings)
        return settings_page

    def update_schedule(self):
        start_time = self.start_time_edit.time().toString("HH:mm")
        end_time = self.end_time_edit.time().toString("HH:mm")
        interval = self.interval_spinbox.value()
        self.schedule_widget.setup_table(interval_minutes=interval, start_time_str=start_time, end_time_str=end_time)

class TaskDialog(QDialog):
    def __init__(self, parent=None, initial_value=""):
        super().__init__(parent)
        self.setWindowTitle("Add / Edit Task")
        self.setFixedSize(300, 150)

        # 對話框佈局
        layout = QVBoxLayout(self)

        # 任務名稱輸入
        form_layout = QFormLayout()
        self.task_name_input = QLineEdit(initial_value)
        form_layout.addRow("Task Name:", self.task_name_input)
        layout.addLayout(form_layout)

        # 對話框按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)  # OK 按鈕
        button_box.rejected.connect(self.reject)  # Cancel 按鈕
        layout.addWidget(button_box)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

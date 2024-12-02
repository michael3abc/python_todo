from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, 
                               QStackedWidget, QTableWidget, QTableWidgetItem, QSizePolicy, QTimeEdit, QSpinBox, 
                               QLineEdit, QFrame, QDialog, QScrollArea, QFormLayout, QDialogButtonBox, QComboBox,QHeaderView,QMessageBox
                               )
from PySide6.QtCore import Qt, QTime, QMimeData
from PySide6.QtGui import QDrag, QColor,QBrush,QPixmap,QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTimeEdit, QSpinBox,
    QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import QTime
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QMimeData

from datetime import datetime, timedelta
import csv
import sys
import os
import json


tagset_filelocation = './tagset_datas.csv'
tagset_filelocation = os.path.abspath('./tagset_datas.csv')

SETTINGS_FILE="./setting.json"






##########################################


class TaskDetailsDialog(QDialog):
    """A dialog to collect additional task details based on tags."""
    def __init__(self, tags, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Task Details")
        self.setFixedSize(400, 300)

        self.tag_inputs = {}  # Dictionary to store tag inputs

        # Layouts
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Task Name
        self.task_name_input = QLineEdit()
        form_layout.addRow("Task Name:", self.task_name_input)

        # Dynamically create input fields for each tag
        for tag in tags:
            tag_name = tag["name"]
            tag_type = tag["type"]

            if tag_type == "int":
                input_field = QSpinBox()
                input_field.setRange(-999999, 999999)
            elif tag_type == "float":
                input_field = QDoubleSpinBox()
                input_field.setRange(-999999.0, 999999.0)
            elif tag_type == "bool":
                input_field = QComboBox()
                input_field.addItems(["True", "False"])
            elif tag_type == "str":
                input_field = QLineEdit()
            else:
                input_field = QLineEdit()  # Default to QLineEdit for unsupported types

            form_layout.addRow(tag_name + ":", input_field)
            self.tag_inputs[tag_name] = input_field

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)


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

class DraggableTask(QLabel):
    """A draggable QLabel representing a task."""
    def __init__(self, task_name, parent=None):
        super().__init__(task_name, parent)
        self.task_name = task_name
        self.setStyleSheet("background-color: lightblue; padding: 5px; border: 1px solid gray;")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(30)

    def mouseMoveEvent(self, event):
        """Handle the drag event when the task is dragged."""
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.task_name)  # Set the task name as drag data
            drag.setMimeData(mime_data)

            # Create a pixmap to use as a drag icon
            pixmap = QPixmap(self.size())  # Use the size of the widget
            pixmap.fill(Qt.transparent)   # Transparent background

            # Paint the task label onto the pixmap
            painter = QPainter(pixmap)
            painter.setOpacity(0.3)  # Set opacity to 50%

            painter.fillRect(self.rect(), self.palette().window())  # Fill with background color
            painter.drawText(self.rect(), Qt.AlignCenter, self.task_name)  # Draw task name
            painter.end()

            drag.setPixmap(pixmap)  # Set the pixmap as the drag icon
            drag.setHotSpot(event.pos())  # Set the hotspot to the cursor position

            drag.exec(Qt.CopyAction | Qt.MoveAction)# Course button widget
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
        self.schedule_table.setAcceptDrops(True)  # Allow drop events
        self.schedule_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(self.schedule_table)

        self.setup_table()
        self.schedule_table.resizeEvent = lambda event: self.adjust_table_sizes()

    def setup_table(self, interval_minutes=30, start_time_str="08:00", end_time_str="17:00"):
        """Set up the schedule table with time intervals and days of the week."""
        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        self.schedule_table.setColumnCount(len(weekdays))
        self.schedule_table.setHorizontalHeaderLabels(weekdays)

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
        self.schedule_table.verticalHeader().setDefaultSectionSize(30)  # Set the default row height

    def dragEnterEvent(self, event):
        """Accept drag events if the data is text."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle the drop event to set the task name in the dropped cell."""
        pos = event.pos()
        row = self.schedule_table.rowAt(pos.y())
        col = self.schedule_table.columnAt(pos.x())

        if row >= 0 and col >= 0 and event.mimeData().hasText():
            task_name = event.mimeData().text()
            item = QTableWidgetItem(task_name)
            item.setTextAlignment(Qt.AlignCenter)
            self.schedule_table.setItem(row, col, item)
            event.acceptProposedAction()
    def adjust_table_sizes(self):
        """Adjust the column widths and row heights to fit the table."""
        total_width = self.schedule_table.viewport().width()
        total_height = self.schedule_table.viewport().height()

        if self.schedule_table.columnCount() > 0:
            column_width = total_width // self.schedule_table.columnCount()
            for col in range(self.schedule_table.columnCount()):
                self.schedule_table.setColumnWidth(col, column_width)

        if self.schedule_table.rowCount() > 0:
            row_height = 30
            for row in range(self.schedule_table.rowCount()):
                self.schedule_table.setRowHeight(row, row_height)





class HoverableBox(QFrame):
    """A custom frame that changes color when hovered and handles drops."""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window  # Reference to the main window
        self.setFixedSize(50, 50)  # Smaller size for the box
        self.setStyleSheet("background-color: lightgray;")
        self.setAcceptDrops(True)  # Allow drop events

    def enterEvent(self, event):
        """Change color when mouse enters."""
        self.setStyleSheet("background-color: lightblue;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Revert color when mouse leaves."""
        self.setStyleSheet("background-color: lightgray;")
        super().leaveEvent(event)

    def dragEnterEvent(self, event):
        """Accept drag events if the data is text."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Show a confirmation dialog when a task is dropped."""
        if event.mimeData().hasText():
            task_name = event.mimeData().text()
            dialog = QMessageBox()
            dialog.setIcon(QMessageBox.Question)
            dialog.setWindowTitle("Remove Task")
            dialog.setText(f"Are you sure you want to remove the task '{task_name}'?")
            dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            dialog.setDefaultButton(QMessageBox.No)
            choice = dialog.exec()

            if choice == QMessageBox.Yes:
                # Call the main window's remove_task method
                self.main_window.remove_task(task_name)
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Schedule Manager")
        self.resize(800, 600)
        self.move(900, 500)
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
        pass
        
    def save_settings(self):
        """Save the current settings (start time, end time, time interval) to a JSON file."""
        settings = {
            "start_time": self.start_time_edit.time().toString("HH:mm"),
            "end_time": self.end_time_edit.time().toString("HH:mm"),
            "time_interval": self.interval_spinbox.value(),
        }
        with open(SETTINGS_FILE, "w") as file:
            json.dump(settings, file)

    def load_settings(self):
        """Load the settings from the JSON file and apply them to the widgets."""
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as file:
                settings = json.load(file)
                # Apply the settings to the widgets
                self.start_time_edit.setTime(QTime.fromString(settings.get("start_time", "08:00"), "HH:mm"))
                self.end_time_edit.setTime(QTime.fromString(settings.get("end_time", "17:00"), "HH:mm"))
                self.interval_spinbox.setValue(settings.get("time_interval", 30))
        else:
            # If the file doesn't exist, set default values
            self.start_time_edit.setTime(QTime(8, 0))
            self.end_time_edit.setTime(QTime(17, 0))
            self.interval_spinbox.setValue(30)

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
        """Load tags data from the CSV and display it in the table."""
        with open(tagset_filelocation, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)

            headers = next(reader)
            self.tags_table.setColumnCount(len(headers) + 1)  # +1 for the delete button column
            self.tags_table.setHorizontalHeaderLabels(headers + ["Delete"])

            for row_data in reader:
                row_position = self.tags_table.rowCount()
                self.tags_table.insertRow(row_position)

                for column, data in enumerate(row_data):
                    if column == 1:  # Type column
                        type_combo = QComboBox()
                        type_combo.addItems(["int", "float", "str", "list", "dict", "bool", "set"])
                        type_combo.setCurrentText(data)
                        self.tags_table.setCellWidget(row_position, column, type_combo)
                    elif column == 3:  # Visibility column
                        visibility_combo = QComboBox()
                        visibility_combo.addItems(["True", "False"])
                        visibility_combo.setCurrentText(data)
                        self.tags_table.setCellWidget(row_position, column, visibility_combo)
                    else:
                        item = QTableWidgetItem(data)
                        self.tags_table.setItem(row_position, column, item)

                # Add delete button
                delete_button = QPushButton("Delete")
                delete_button.clicked.connect(self.delete_row)
                self.tags_table.setCellWidget(row_position, len(headers), delete_button)

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

        for column in range(self.tags_table.columnCount() - 1):  # Exclude the delete button column
            if column == 1:  # Type column
                type_combo = QComboBox()
                type_combo.addItems(["int", "float", "str", "list", "dict", "bool", "set"])
                self.tags_table.setCellWidget(row_position, column, type_combo)
            elif column == 3:  # Visibility column
                visibility_combo = QComboBox()
                visibility_combo.addItems(["True", "False"])
                self.tags_table.setCellWidget(row_position, column, visibility_combo)
            else:
                input_field = QLineEdit()
                input_field.setAlignment(Qt.AlignLeft)
                self.tags_table.setCellWidget(row_position, column, input_field)

        # Add delete button
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_row)
        self.tags_table.setCellWidget(row_position, self.tags_table.columnCount() - 1, delete_button)


    def delete_row(self):
        """Delete the row containing the clicked delete button."""
        button = self.sender()  # Get the button that was clicked
        if button:
            # Find the row containing this button
            for row in range(self.tags_table.rowCount()):
                if self.tags_table.cellWidget(row, self.tags_table.columnCount() - 1) == button:
                    self.tags_table.removeRow(row)
                    print(row)
                    break

    def save_tags_data(self):
        """Save the tags data to a CSV file, excluding the last column (delete button)."""
        with open(tagset_filelocation, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Get the header
            headers = [self.tags_table.horizontalHeaderItem(col).text() for col in range(self.tags_table.columnCount() - 1)]
            writer.writerow(headers)

            # Write rows
            for row in range(self.tags_table.rowCount()):
                row_data = []
                for column in range(self.tags_table.columnCount() - 1):  # Exclude the delete button column
                    widget = self.tags_table.cellWidget(row, column)
                    if isinstance(widget, QComboBox):  # For combo boxes
                        row_data.append(widget.currentText())
                    elif isinstance(widget, QLineEdit):  # For line edits
                        row_data.append(widget.text())
                    else:  # For standard table items
                        item = self.tags_table.item(row, column)
                        row_data.append(item.text() if item else "")
                writer.writerow(row_data)
##################################                
    def create_tasks_page(self):
        """
        Create the Tasks Page with an "Add Task" button and a smaller hoverable box next to it.
        """
        tasks_page = QWidget()
        tasks_layout = QVBoxLayout(tasks_page)

        # Scroll area for tasks
        self.task_scroll_area = QScrollArea()
        self.task_scroll_area.setWidgetResizable(True)
        self.task_scroll_content = QWidget()
        self.task_scroll_layout = QVBoxLayout(self.task_scroll_content)
        self.task_scroll_area.setWidget(self.task_scroll_content)

        # Add the scroll area to the tasks layout
        tasks_layout.addWidget(self.task_scroll_area)

        # Horizontal layout for the "Add Task" button and hoverable box
        action_layout = QHBoxLayout()

        # "Add Task" button
        add_task_button = QPushButton("Add Task")
        add_task_button.setStyleSheet("background-color: lightgray; font-size: 14px;")
        add_task_button.clicked.connect(self.open_task_dialog)
        action_layout.addWidget(add_task_button)

        # Hoverable Box (pass self as the main window reference)
        hoverable_box = HoverableBox(self)
        action_layout.addWidget(hoverable_box)

        # Add the action layout to the tasks layout
        tasks_layout.addLayout(action_layout)

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
        """Add a draggable task to the Tasks Page."""
        task = DraggableTask(task_name)
        self.task_scroll_layout.insertWidget(0, task)
        self.task_scroll_content.updateGeometry()


        
    def remove_task(self, task_name):
        """Remove a task by its name."""
        for i in range(self.task_scroll_layout.count()):
            widget = self.task_scroll_layout.itemAt(i).widget()
            if isinstance(widget, DraggableTask) and widget.task_name == task_name:
                widget.deleteLater()
                break

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
        # Create the main settings page widget and layout
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)

        # Create the top section for time settings
        time_settings = QWidget()
        time_layout = QVBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(15)

        # Start Time
        start_time_container = QWidget()
        start_time_layout = QHBoxLayout()
        start_time_layout.setContentsMargins(0, 0, 0, 0)
        start_time_label = QLabel("開始時間:")
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm")  # Set the time display format
        self.start_time_edit.setWrapping(True)  # Allow wrapping around limits
        start_time_layout.addWidget(start_time_label)
        start_time_layout.addWidget(self.start_time_edit)
        start_time_container.setLayout(start_time_layout)

        # End Time
        end_time_container = QWidget()
        end_time_layout = QHBoxLayout()
        end_time_layout.setContentsMargins(0, 0, 0, 0)
        end_time_label = QLabel("結束時間:")
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm")  # Set the time display format
        self.end_time_edit.setWrapping(True)  # Allow wrapping around limits
        end_time_layout.addWidget(end_time_label)
        end_time_layout.addWidget(self.end_time_edit)
        end_time_container.setLayout(end_time_layout)

        # Time Interval
        interval_container = QWidget()
        interval_layout = QHBoxLayout()
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_label = QLabel("時間間隔(分鐘):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(5, 60)  # Allow intervals from 5 to 60 minutes
        self.interval_spinbox.setSingleStep(5)  # Adjust by 5 minutes per click
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)
        interval_container.setLayout(interval_layout)

        # Add start time, end time, and interval to the layout
        time_layout.addWidget(start_time_container)
        time_layout.addWidget(end_time_container)
        time_layout.addWidget(interval_container)
        time_settings.setLayout(time_layout)

        # Horizontal Line
        horizontal_line = QFrame()
        horizontal_line.setFrameShape(QFrame.HLine)
        horizontal_line.setFrameShadow(QFrame.Sunken)
        horizontal_line.setFixedHeight(2)  # Adjust line thickness

        # Spacer below the time settings to push the line higher
        spacer_below_settings = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)  # Fixed size spacer

        # Update Button
        update_button = QPushButton("更新課表")
        update_button.clicked.connect(self.update_schedule)  # Update the schedule
        update_button.clicked.connect(self.save_settings)    # Save settings to file

        # Spacer below the line
        spacer_below = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Layout for the line and update button
        line_and_button_layout = QVBoxLayout()
        line_and_button_layout.addSpacerItem(spacer_below_settings)  # Add spacer to push the line higher
        line_and_button_layout.addWidget(horizontal_line)
        line_and_button_layout.addSpacerItem(spacer_below)
        line_and_button_layout.addWidget(update_button)

        # Add everything to the main settings layout
        settings_layout.addWidget(time_settings)  # Add time settings above the line
        settings_layout.addLayout(line_and_button_layout)

        # Load settings on startup
        self.load_settings()

        return settings_page


    def update_schedule(self):
        """Update the schedule table based on the settings."""
        start_time = self.start_time_edit.time().toString("HH:mm")
        end_time = self.end_time_edit.time().toString("HH:mm")
        interval = self.interval_spinbox.value()

        # Call the setup_table method to apply the new settings
        self.schedule_widget.setup_table(interval_minutes=interval, start_time_str=start_time, end_time_str=end_time)

        # Adjust the table sizes after updating
        self.schedule_widget.adjust_table_sizes()

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
    window.update_schedule()
    window.show()
    sys.exit(app.exec())

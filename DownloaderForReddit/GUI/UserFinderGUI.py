"""
Downloader for Reddit takes a list of reddit users and subreddits and downloads content posted to reddit either by the
users or on the subreddits.


Copyright (C) 2017, Kyle Hickey


This file is part of the Downloader for Reddit.

Downloader for Reddit is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Downloader for Reddit is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Downloader for Reddit.  If not, see <http://www.gnu.org/licenses/>.
"""


from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWebEngineWidgets import QWebEngineView

from GUI_Resources.UserFinderGUI_auto import Ui_UserFinderGUI
from UserFinder.UserFinder import UserFinder
from Core import Injector
from GUI.AddUserDialog import AddUserDialog
from GUI.UserFinderSettingsGUI import UserFinderSettingsGUI
from ViewModels.UserFinderListModel import UserFinderListModel


class UserFinderGUI(QtWidgets.QWidget, Ui_UserFinderGUI):

    closed = QtCore.pyqtSignal()

    def __init__(self, user_view_chooser_dict):
        QtWidgets.QWidget.__init__(self)
        self.setupUi(self)
        self.user_view_chooser_dict = user_view_chooser_dict
        self.running = False
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.content_list_init_setup = False

        self.user_list_model = UserFinderListModel()
        self.user_list_view.setModel(self.user_list_model)

        self.view_users_button.clicked.connect(self.change_page)
        self.settings_button.clicked.connect(self.open_user_finder_settings)
        self.run_button.clicked.connect(self.run_user_finder)
        self.user_finder_button.clicked.connect(self.change_page)

        self.add_subreddit_button.clicked.connect(self.add_subreddit)
        self.remove_subreddit_button.clicked.connect(self.remove_subreddit)
        self.add_user_button.clicked.connect(self.add_blacklist_user)
        self.remove_user_button.clicked.connect(self.remove_user_from_blacklist)

        self.settings_manager = Injector.get_settings_manager()
        geom = self.settings_manager.user_finder_GUI_geom
        self.restoreGeometry(geom if geom is not None else self.saveGeometry())
        splitter_one_state = self.settings_manager.user_finder_splitter_one_state
        splitter_two_state = self.settings_manager.user_finder_splitter_two_state
        splitter_three_state = self.settings_manager.user_finder_splitter_three_state
        self.splitter_one.restoreState(splitter_one_state if splitter_one_state else self.splitter_one.saveState())
        self.splitter_two.restoreState(splitter_two_state if splitter_two_state else self.splitter_two.saveState())
        self.splitter_three.restoreState(splitter_three_state if splitter_three_state else
                                         self.splitter_three.saveState())

        if 'filler' in self.settings_manager.user_finder_subreddit_list:
            self.settings_manager.user_finder_subreddit_list.remove('filler')
        if 'filler' in self.settings_manager.user_finder_user_blacklist:
            self.settings_manager.user_finder_user_blacklist.remove('filler')

        for item in self.settings_manager.user_finder_subreddit_list:
            self.subreddit_watchlist_widget.addItem(item)

        for item in self.settings_manager.user_finder_user_blacklist:
            self.user_blacklist_widget.addItem(item)

        self.top_sort_radio_dict = {
            'HOUR': self.hour_radio,
            'DAY': self.day_radio,
            'WEEK': self.week_radio,
            'MONTH': self.month_radio,
            'YEAR': self.year_radio,
            'ALL': self.all_time_radio
        }

        self.top_sort_radio_dict[self.settings_manager.user_finder_top_sort_method].setChecked(True)
        self.filter_by_score_checkbox.setChecked(self.settings_manager.user_finder_filter_by_score)
        self.score_limit_spinbox.setValue(self.settings_manager.user_finder_score_limit)
        self.post_limit_spinbox.setValue(self.settings_manager.user_finder_post_limit)

        self.preview_size = self.settings_manager.user_finder_preview_size
        self.user_list_sort_method = self.settings_manager.user_finder_user_list_sort_method
        self.user_list_sort_order = self.settings_manager.user_finder_user_list_sort_order

        self.subreddit_watchlist_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.subreddit_watchlist_widget.customContextMenuRequested.connect(self.subreddit_watchlist_right_click)

        self.user_blacklist_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.user_blacklist_widget.customContextMenuRequested.connect(self.user_blacklist_right_click)

        self.user_list_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.user_list_view.customContextMenuRequested.connect(self.user_list_right_click)

        self.content_list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.content_list_widget.customContextMenuRequested.connect(self.content_list_right_click)

        self.user_list_view.clicked.connect(self.change_display_user)

        self.user_post_count_label.clicked.connect(self.get_user_post_count)

    # region PageOne

    def change_page(self):
        if self.stacked_widget.currentIndex() == 0:
            self.stacked_widget.setCurrentIndex(1)
            if not self.content_list_init_setup:
                self.set_initial_content_list()
            self.set_user_post_count_label()
        else:
            self.stacked_widget.setCurrentIndex(0)

    def subreddit_watchlist_right_click(self):
        pass
        # TODO: make this context menu

    def user_blacklist_right_click(self):
        pass
        # TODO: Make this context menu

    def add_subreddit(self):
        dialog = AddUserDialog()
        dialog.add_another_button.clicked.connect(lambda: self.add_subreddit_to_list(dialog.name))
        dialog.show()
        reply = dialog.exec_()
        if reply == QtWidgets.QDialog.Accepted:
            self.add_subreddit_to_list(dialog.name)

    def add_subreddit_to_list(self, subreddit):
        if subreddit != '' and subreddit != ' ' and subreddit not in self.get_subreddit_items():
            self.subreddit_watchlist_widget.addItem(subreddit)

    def remove_subreddit(self):
        self.subreddit_watchlist_widget.takeItem(self.subreddit_watchlist_widget.currentIndex().row())

    def add_blacklist_user(self):
        dialog = AddUserDialog()
        dialog.add_another_button.clicked.connect(lambda: self.add_user_to_blacklist(dialog.name))
        dialog.show()
        reply = dialog.exec_()
        if reply == QtWidgets.QDialog.Accepted:
            self.add_user_to_blacklist(dialog.name)

    def add_user_to_blacklist(self, user):
        if user != '' and user != ' ' and user not in self.get_user_blacklist_items():
            self.user_blacklist_widget.addItem(user)

    def remove_user_from_blacklist(self):
        self.user_blacklist_widget.takeItem(self.user_blacklist_widget.currentIndex().row())

    def run_user_finder(self):
        self.save_settings()
        self.thread = QtCore.QThread()
        self.user_finder = UserFinder(self.get_subreddit_items(), self.get_user_blacklist_items(),
                                      self.user_view_chooser_dict)
        self.user_finder.moveToThread(self.thread)
        self.thread.started.connect(self.user_finder.run)
        self.user_finder.send_user.connect(self.add_found_user)
        self.user_finder.finished.connect(self.thread.quit)
        self.user_finder.finished.connect(self.user_finder.deleteLater)
        self.thread.finished.connect(self.complete)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def complete(self):
        print('User Finder Done')

    def add_found_user(self, user):
        self.add_user_to_list(user)
        print('User Found: %s' % user.name)

    def open_user_finder_settings(self):
        dialog = UserFinderSettingsGUI()
        dialog.show()
        dialog.exec_()

    def get_top_sort_method(self):
        for key, value in self.top_sort_radio_dict.items():
            if value.isChecked():
                return key

    def get_sample_method(self):
        for key, value in self.sample_method_radio_dict.items():
            if value.isChecked():
                return key

    def closeEvent(self, QCloseEvent):
        self.closed.emit()
        self.save_settings()

    def save_settings(self):
        self.settings_manager.user_finder_GUI_geom = self.saveGeometry()
        self.settings_manager.user_finder_splitter_one_state = self.splitter_one.saveState()
        self.settings_manager.user_finder_splitter_two_state = self.splitter_two.saveState()
        self.settings_manager.user_finder_splitter_three_state = self.splitter_three.saveState()
        self.settings_manager.user_finder_top_sort_method = self.get_top_sort_method()
        self.settings_manager.user_finder_filter_by_score = self.filter_by_score_checkbox.isChecked()
        self.settings_manager.user_finder_score_limit = self.score_limit_spinbox.value()
        self.settings_manager.user_finder_post_limit = self.post_limit_spinbox.value()
        self.settings_manager.user_finder_subreddit_list = self.get_subreddit_items()
        self.settings_manager.user_finder_user_blacklist = self.get_user_blacklist_items()
        self.settings_manager.user_finder_preview_size = self.preview_size
        self.settings_manager.user_finder_user_list_sort_method = self.user_list_sort_method
        self.settings_manager.user_finder_user_list_sort_order = self.user_list_sort_order
        self.settings_manager.save_user_finder_dialog()

    def get_subreddit_items(self):
        sub_list = []
        for x in range(self.subreddit_watchlist_widget.count()):
            sub_list.append(self.subreddit_watchlist_widget.item(x).text())
        return sub_list

    def get_user_blacklist_items(self):
        user_list = []
        for x in range(self.user_blacklist_widget.count()):
            user_list.append(self.user_blacklist_widget.item(x).text())
        return user_list

    # endregion

    # region PageTwo

    def add_user_to_list(self, user):
        self.user_list_model.add_user(user)
        self.user_list_model.sort_lists((self.user_list_sort_method, self.user_list_sort_order))

    def change_display_user(self):
        row = self.user_list_view.currentIndex().row()
        user = self.user_list_model.user_list[row]
        self.setup_content_list(user)
        self.set_user_post_count_label()

    def set_initial_content_list(self):
        try:
            user = self.user_list_model.user_list[0]
            self.setup_content_list(user)
        except IndexError:
            pass

    def setup_content_list(self, user):
        self.content_list_widget.clear()
        for content in user.content:
            item = QtWidgets.QListWidgetItem()
            item.setText(content.post_title)
            size = self.preview_size
            item.setSizeHint(QtCore.QSize(size, size))
            web_view = QWebEngineView()
            web_view.load(QtCore.QUrl(content.url))
            web_view.setMinimumWidth(size)
            web_view.setMinimumHeight(size)
            self.content_list_widget.addItem(item)
            self.content_list_widget.setItemWidget(item, web_view)

    def user_list_right_click(self):
        menu = QtWidgets.QMenu()
        self.add_sort_menus(menu)
        menu.addSeparator()
        add_to_user_list_menu = menu.addMenu('Add User To List')
        default_list = add_to_user_list_menu.addAction('Auto Add List')
        default_list.setToolTip('The auto add to list as defined in the user finder settings dialog.')
        default_list.triggered.connect(lambda: self.add_user_to_main_winodw_user_list(
            self.settings_manager.user_finder_auto_add_user_list))

        # TODO: Figure out how to add to multiple list options from menu

        menu.addSeparator()
        add_user_to_blacklist = menu.addAction('Add To Blacklist')
        remove_user = menu.addAction('Remove From List')

        add_user_to_blacklist.triggered.connect(self.add_user_to_blacklist_from_found_users)
        remove_user.triggered.connect(self.remove_user_from_found_list)
        menu.exec(QtGui.QCursor.pos())

    def add_sort_menus(self, menu):
        sort_menu = menu.addMenu('Sort Method')
        sort_name = sort_menu.addAction('Name')
        sort_karma = sort_menu.addAction('Karma')
        sort_date = sort_menu.addAction('Last Post Date')

        sort_name.setCheckable(True)
        sort_karma.setCheckable(True)
        sort_date.setCheckable(True)

        sort_name.triggered.connect(lambda: self.set_user_list_sort_method('NAME'))
        sort_karma.triggered.connect(lambda: self.set_user_list_sort_method('KARMA'))
        sort_date.triggered.connect(lambda: self.set_user_list_sort_method('POST_DATE'))

        sort_method_group = QtWidgets.QActionGroup(self)
        sort_method_group.addAction(sort_name)
        sort_method_group.addAction(sort_karma)
        sort_method_group.addAction(sort_date)

        sort_order_menu = menu.addMenu('Sort Order')
        sort_asc = sort_order_menu.addAction('Asc')
        sort_desc = sort_order_menu.addAction('Desc')

        sort_asc.setCheckable(True)
        sort_desc.setCheckable(True)

        sort_asc.triggered.connect(lambda: self.set_user_list_sort_order('ASC'))
        sort_desc.triggered.connect(lambda: self.set_user_list_sort_order('DESC'))

        sort_order_group = QtWidgets.QActionGroup(self)
        sort_order_group.addAction(sort_asc)
        sort_order_group.addAction(sort_desc)

        sort_method_dict = {
            'NAME': sort_name,
            'KARMA': sort_karma,
            'POST_DATE': sort_date
        }

        sort_order_dict = {
            'ASC': sort_asc,
            'DESC': sort_desc
        }

        sort_method_dict[self.user_list_sort_method].setChecked(True)
        sort_order_dict[self.user_list_sort_order].setChecked(True)

    def content_list_right_click(self):
        menu = QtWidgets.QMenu()

        open_content = menu.addAction('Open Item')
        menu.addSeparator()
        icon_extra_small = menu.addAction('Extra Small')
        icon_small = menu.addAction('Small')
        icon_medium = menu.addAction('Medium')
        icon_large = menu.addAction('Large')
        icon_extra_large = menu.addAction('Extra Large')
        icon_original = menu.addAction('Original')

        icon_extra_small.setCheckable(True)
        icon_small.setCheckable(True)
        icon_medium.setCheckable(True)
        icon_large.setCheckable(True)
        icon_extra_large.setCheckable(True)
        icon_original.setCheckable(True)

        open_content.triggered.connect(self.open_content_item)
        icon_extra_small.triggered.connect(lambda: self.set_preview_size(48))
        icon_small.triggered.connect(lambda: self.set_preview_size(72))
        icon_medium.triggered.connect(lambda: self.set_preview_size(110))
        icon_large.triggered.connect(lambda: self.set_preview_size(176))
        icon_extra_large.triggered.connect(lambda: self.set_preview_size(256))
        icon_original.triggered.connect(lambda: self.set_preview_size(0))

        size_group = QtWidgets.QActionGroup(self)
        size_group.addAction(icon_extra_small)
        size_group.addAction(icon_small)
        size_group.addAction(icon_medium)
        size_group.addAction(icon_large)
        size_group.addAction(icon_extra_large)
        size_group.addAction(icon_original)

        icon_dict = {
            48: icon_extra_small,
            72: icon_small,
            110: icon_medium,
            176: icon_large,
            256: icon_extra_large,
            0: icon_original
        }

        icon_dict[self.preview_size].setChecked(True)

        menu.exec(QtGui.QCursor.pos())

    def get_user_post_count(self):
        """
        Starts a thread and a user finder instance to connect to reddit and get the currently selected users post count.
        """
        try:
            user = self.user_list_model.user_list[self.user_list_view.currentIndex().row()].name
            self.thread = QtCore.QThread()
            self.user_finder = UserFinder(None, None, None)
            self.user_finder.user_post_count_signal.connect(self.set_user_post_count)
            self.thread.started.connect(lambda: self.user_finder.get_user_count(user))
            self.user_finder.finished.connect(self.thread.quit)
            self.user_finder.finished.connect(self.user_finder.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()
        except IndexError:
            pass

    def set_user_post_count(self, count_tuple):
        """
        Sets the currently selected users post count attribute according to the count_tuple sent via signal from the
        user finder thread.
        :param count_tuple: A tuple containing the post count for the current user and the users name
        :return:
        """
        for user in self.user_list_model.user_list:
            if user.name == count_tuple[1]:
                user.post_count = count_tuple[0]
                self.set_user_post_count_label()
                break

    def set_user_post_count_label(self):
        """
        Sets the user post count label based on whether or not the currently selected user has a post count value.
        """
        try:
            user = self.user_list_model.user_list[self.user_list_view.currentIndex().row()]
            if user.post_count:
                self.user_post_count_label.setText(str(user.post_count))
                self.user_post_count_label.setStyleSheet('color: black')
            else:
                self.user_post_count_label.setText('Click For Post Count')
                self.user_post_count_label.setToolTip('This count is not retrieved automatically because it may take '
                                                      'some time')
                self.user_post_count_label.setStyleSheet('color: blue')
        except IndexError:
            self.user_post_count_label.setText('Select User For Post Count')
            self.user_post_count_label.setStyleSheet('color: black')

    def add_user_to_main_winodw_user_list(self, list):
        print(list)

    def add_user_to_blacklist_from_found_users(self):
        user = self.user_list_model.user_list[self.user_list_view.currentIndex().row()]
        self.add_user_to_blacklist(user.name)

    def remove_user_from_found_list(self):
        self.user_list_model.removeRow(self.user_list_view.currentIndex().row())

    def open_content_item(self):
        pass

    def set_preview_size(self, size):
        self.preview_size = size
        # TODO: Set all loaded content size to this

    def set_user_list_sort_method(self, method):
        self.user_list_sort_method = method
        self.user_list_model.sort_lists((method, self.user_list_sort_order))

    def set_user_list_sort_order(self, order):
        self.user_list_sort_order = order
        self.user_list_model.sort_lists((self.user_list_sort_method, order))

    # endregion



































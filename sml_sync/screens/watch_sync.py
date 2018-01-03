
import collections

from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout import HSplit
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.key_binding.key_bindings import KeyBindings

from ..pubsub import Messages
from ..models import ChangeEventType


class WatchSyncScreen(object):

    def __init__(self, exchange):
        self._exchange = exchange

        self._held_files = []
        self._recently_synced_items = collections.deque(maxlen=10)
        self._current_event = None

        self._loading_status_control = FormattedTextControl('Loading...')
        self._queue_status_control = FormattedTextControl('')
        self._recently_synced_items_control = FormattedTextControl('')
        self._held_files_control = FormattedTextControl('')

        self.menu_bar = Window(FormattedTextControl(
                '[s] Stop  '
                '[q] Quit'
            ), height=1, style='reverse')

        self.main_container = HSplit([
            Window(self._loading_status_control),
            self.menu_bar
        ])
        self._exchange.subscribe(
            'START_WATCH_SYNC_MAIN_LOOP',
            lambda _: self._update_main_screen()
        )
        self._exchange.subscribe(
            Messages.HELD_FILES_CHANGED,
            lambda held_files: self._update_held_files(held_files)
        )
        self._exchange.subscribe(
            Messages.STARTING_HANDLING_FS_EVENT,
            lambda event: self._on_start_handling_fs_event(event)
        )
        self._exchange.subscribe(
            Messages.FINISHED_HANDLING_FS_EVENT,
            lambda event: self._on_finish_handling_fs_event(event)
        )

        self.bindings = KeyBindings()

        @self.bindings.add('s')
        def _(event):
            self._exchange.publish(Messages.STOP_WATCH_SYNC)

    def _update_main_screen(self):
        self._update_recently_synced_items_control()
        self._update_held_files_control()
        self.main_container.children = [
            Window(self._queue_status_control, height=1),
            Window(self._recently_synced_items_control, height=10),
            Window(char='-', height=1),
            Window(FormattedTextControl(
                'The following files will not be synced '
                'to avoid accidentally overwriting changes on SherlockML:'),
                dont_extend_height=True
            ),
            Window(self._held_files_control),
            self.menu_bar
        ]

    def _update_held_files(self, held_files):
        self._held_files = held_files
        self._update_held_files_control()

    def _on_start_handling_fs_event(self, fs_event):
        self._current_event = fs_event
        self._update_queue_status()

    def _on_finish_handling_fs_event(self, fs_event):
        self._current_event = None
        self._recently_synced_items.appendleft(fs_event)
        self._update_queue_status()
        self._update_recently_synced_items_control()

    def _update_recently_synced_items_control(self):
        recent_syncs_text = [
            '  {}'.format(self._format_fs_event(fs_event))
            for fs_event in self._recently_synced_items
        ]
        self._recently_synced_items_control.text = '\n'.join(recent_syncs_text)

    def _format_fs_event(self, event):
        if event.event_type == ChangeEventType.MOVED:
            src_path = event.path
            dest_path = event.extra_args['dest_path']
            event_str = '> {} -> {}'.format(src_path, dest_path)
        elif event.event_type == ChangeEventType.DELETED:
            event_str = 'x {}'.format(event.path)
        else:
            event_str = '> {}'.format(event.path)
        return event_str

    def _update_queue_status(self):
        if self._current_event is not None:
            path = self._current_event.path
            self._queue_status_control.text = '>>> {}'.format(path)
        else:
            self._queue_status_control.text = ''

    def _update_held_files_control(self):
        held_files_text = [
            '  x {}'.format(held_file) for held_file in self._held_files
        ]
        self._held_files_control.text = '\n'.join(held_files_text)

    def stop(self):
        pass


import os
import math
import threading
import wave
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import mido
import numpy as np
import librosa
import sounddevice as sd


class MusicLab:
    def __init__(self, root):
        self.root = root
        self.root.title("MusicLab")
        self.root.geometry("1280x800")
        self.root.minsize(1050, 650)
        self.root.configure(bg="#101216")

        self.bg = "#101216"
        self.sidebar_bg = "#171a21"
        self.panel = "#1c2028"
        self.panel_light = "#262b35"
        self.accent = "#6c63ff"
        self.accent_hover = "#817aff"
        self.text = "#ffffff"
        self.muted = "#9da4b3"
        self.border = "#303641"
        self.good = "#42d392"
        self.warn = "#f5b942"
        self.bad = "#ff6378"

        self.current_midi = None
        self.current_midi_path = None
        self.current_track = 0
        self.visual_zoom = 1.0

        self.practice_audio = None
        self.practice_sr = 22050
        self.practice_path = None
        self.practice_reference = None

        self.chord_progression = []

        self.pages = {}
        self.nav_buttons = {}

        self.configure_styles()
        self.build_ui()
        self.show_page("home")

    def configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background=self.panel,
            fieldbackground=self.panel,
            foreground=self.text,
            borderwidth=0,
            rowheight=30
        )
        style.configure(
            "Treeview.Heading",
            background=self.panel_light,
            foreground=self.text,
            relief="flat"
        )
        style.configure(
            "TCombobox",
            fieldbackground=self.panel_light,
            background=self.panel_light,
            foreground=self.text,
            arrowcolor=self.text
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.panel_light)],
            foreground=[("readonly", self.text)]
        )

    def build_ui(self):
        self.sidebar = tk.Frame(
            self.root,
            width=235,
            bg=self.sidebar_bg
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="MusicLab",
            font=("Segoe UI", 24, "bold"),
            bg=self.sidebar_bg,
            fg=self.text
        ).pack(pady=(30, 25))

        self.add_nav("Home", "home")
        self.add_nav("MIDI Studio", "midi")
        self.add_nav("MIDI Visualiser", "visualiser")
        self.add_nav("Practice Analyser", "practice")
        self.add_nav("Chord Generator", "chords")

        tk.Label(
            self.sidebar,
            text="V5.0",
            font=("Segoe UI", 8),
            bg=self.sidebar_bg,
            fg="#6f7684"
        ).pack(side="bottom", pady=15)

        self.main = tk.Frame(self.root, bg=self.bg)
        self.main.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(self.main, bg=self.bg)
        self.content.pack(fill="both", expand=True, padx=25, pady=25)

        self.status = tk.Label(
            self.main,
            text="Ready",
            anchor="w",
            bg="#0c0e12",
            fg=self.muted,
            padx=15,
            pady=6,
            font=("Segoe UI", 9)
        )
        self.status.pack(side="bottom", fill="x")

    def add_nav(self, text, page):
        button = tk.Button(
            self.sidebar,
            text=text,
            command=lambda: self.show_page(page),
            font=("Segoe UI", 11),
            bg=self.sidebar_bg,
            fg=self.muted,
            activebackground=self.accent,
            activeforeground=self.text,
            relief="flat",
            bd=0,
            anchor="w",
            padx=25,
            pady=12,
            cursor="hand2"
        )
        button.pack(fill="x")
        self.nav_buttons[page] = button

    def show_page(self, page):
        for widget in self.content.winfo_children():
            widget.destroy()

        for name, button in self.nav_buttons.items():
            button.configure(
                bg=self.accent if name == page else self.sidebar_bg,
                fg=self.text if name == page else self.muted
            )

        if page == "home":
            self.home_page()
        elif page == "midi":
            self.midi_page()
        elif page == "visualiser":
            self.visualiser_page()
        elif page == "practice":
            self.practice_page()
        elif page == "chords":
            self.chords_page()

    def card(self, parent):
        return tk.Frame(
            parent,
            bg=self.panel,
            highlightbackground=self.border,
            highlightthickness=1
        )

    def button(self, parent, text, command, primary=True):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=self.accent if primary else self.panel_light,
            fg=self.text,
            activebackground=self.accent_hover if primary else "#333946",
            activeforeground=self.text,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=8
        )

    def status_text(self, text):
        self.status.configure(text=text)

    # ---------------- Home ----------------

    def home_page(self):
        top = self.card(self.content)
        top.pack(fill="x", pady=(0, 18))

        tk.Label(
            top,
            text="Choose a workspace",
            font=("Segoe UI", 18, "bold"),
            bg=self.panel,
            fg=self.text
        ).pack(anchor="w", padx=22, pady=(20, 3))

        tk.Label(
            top,
            text="MIDI tools, visualisation, chord creation and performance analysis.",
            font=("Segoe UI", 10),
            bg=self.panel,
            fg=self.muted
        ).pack(anchor="w", padx=22, pady=(0, 20))

        grid = tk.Frame(self.content, bg=self.bg)
        grid.pack(fill="both", expand=True)

        items = [
            ("MIDI Studio",
             "Import MIDI files and inspect tempo, tracks and notes.",
             "midi"),
            ("MIDI Visualiser",
             "See individual notes on a scrollable piano roll.",
             "visualiser"),
            ("Practice Analyser",
             "Compare a recording against a MIDI reference and score it.",
             "practice"),
            ("Chord Generator",
             "Create progressions and export them as MIDI.",
             "chords")
        ]

        for i, (title, description, page) in enumerate(items):
            row, col = divmod(i, 2)

            grid.grid_rowconfigure(row, weight=1)
            grid.grid_columnconfigure(col, weight=1)

            frame = self.card(grid)
            frame.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=8,
                pady=8
            )

            tk.Label(
                frame,
                text=title,
                font=("Segoe UI", 15, "bold"),
                bg=self.panel,
                fg=self.text
            ).pack(anchor="w", padx=20, pady=(22, 6))

            tk.Label(
                frame,
                text=description,
                wraplength=400,
                justify="left",
                font=("Segoe UI", 9),
                bg=self.panel,
                fg=self.muted
            ).pack(anchor="w", padx=20)

            self.button(
                frame,
                "Open",
                lambda p=page: self.show_page(p)
            ).pack(anchor="w", padx=20, pady=18)

    # ---------------- MIDI ----------------

    def midi_page(self):
        toolbar = tk.Frame(self.content, bg=self.bg)
        toolbar.pack(fill="x", pady=(0, 15))

        self.button(
            toolbar, "Open MIDI File", self.open_midi
        ).pack(side="left")

        self.button(
            toolbar,
            "Open Visualiser",
            lambda: self.show_page("visualiser"),
            primary=False
        ).pack(side="left", padx=10)

        self.midi_file_label = tk.Label(
            toolbar,
            text="No file loaded",
            font=("Segoe UI", 9),
            bg=self.bg,
            fg=self.muted
        )
        self.midi_file_label.pack(side="left")

        stats = tk.Frame(self.content, bg=self.bg)
        stats.pack(fill="x", pady=(0, 15))

        self.midi_stats = {}
        for title, key in [
            ("Tracks", "tracks"),
            ("Notes", "notes"),
            ("BPM", "bpm"),
            ("Length", "length")
        ]:
            frame = self.card(stats)
            frame.pack(
                side="left",
                fill="both",
                expand=True,
                padx=5
            )

            tk.Label(
                frame,
                text=title,
                bg=self.panel,
                fg=self.muted,
                font=("Segoe UI", 9)
            ).pack(anchor="w", padx=15, pady=(12, 0))

            value = tk.Label(
                frame,
                text="—",
                bg=self.panel,
                fg=self.text,
                font=("Segoe UI", 20, "bold")
            )
            value.pack(anchor="w", padx=15, pady=(2, 12))
            self.midi_stats[key] = value

        table = self.card(self.content)
        table.pack(fill="both", expand=True)

        columns = ("track", "name", "channel", "notes", "program")
        self.midi_tree = ttk.Treeview(
            table,
            columns=columns,
            show="headings"
        )

        headings = {
            "track": "Track",
            "name": "Name",
            "channel": "Channel",
            "notes": "Notes",
            "program": "Program"
        }

        for col, heading in headings.items():
            self.midi_tree.heading(col, text=heading)

        self.midi_tree.column("track", width=65, anchor="center")
        self.midi_tree.column("name", width=280)
        self.midi_tree.column("channel", width=90, anchor="center")
        self.midi_tree.column("notes", width=90, anchor="center")
        self.midi_tree.column("program", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(
            table,
            orient="vertical",
            command=self.midi_tree.yview
        )
        self.midi_tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.midi_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(15, 0),
            pady=15
        )
        scrollbar.pack(
            side="right",
            fill="y",
            padx=(0, 15),
            pady=15
        )

    def open_midi(self):
        path = filedialog.askopenfilename(
            title="Open MIDI File",
            filetypes=[
                ("MIDI files", "*.mid *.midi"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:
            self.current_midi = mido.MidiFile(path)
            self.current_midi_path = path
            self.current_track = 0
            self.visual_zoom = 1.0

            notes = self.extract_midi_notes(self.current_midi)
            tempos = self.get_tempo_events(self.current_midi)

            bpm = 120
            if tempos:
                bpm = mido.tempo2bpm(tempos[0][1])

            self.midi_stats["tracks"].configure(
                text=str(len(self.current_midi.tracks))
            )
            self.midi_stats["notes"].configure(
                text=str(len(notes))
            )
            self.midi_stats["bpm"].configure(
                text=f"{bpm:.1f}"
            )
            self.midi_stats["length"].configure(
                text=self.format_duration(self.current_midi.length)
            )

            self.midi_file_label.configure(
                text=os.path.basename(path)
            )

            for item in self.midi_tree.get_children():
                self.midi_tree.delete(item)

            for index, track in enumerate(
                self.current_midi.tracks
            ):
                name = "Unnamed"
                note_count = 0
                channel = "—"
                program = "—"

                for message in track:
                    if message.type == "track_name":
                        name = message.name

                    if (
                        message.type == "note_on"
                        and message.velocity > 0
                    ):
                        note_count += 1

                    if hasattr(message, "channel"):
                        channel = str(message.channel + 1)

                    if message.type == "program_change":
                        program = str(message.program)

                self.midi_tree.insert(
                    "",
                    "end",
                    values=(
                        index + 1,
                        name,
                        channel,
                        note_count,
                        program
                    )
                )

            self.status_text(
                f"Loaded {os.path.basename(path)}"
            )

        except Exception as error:
            messagebox.showerror(
                "MIDI Error",
                f"Could not open this MIDI file.\n\n{error}"
            )

    def get_tempo_events(self, midi):
        events = []
        for track in midi.tracks:
            absolute = 0
            for msg in track:
                absolute += msg.time
                if msg.type == "set_tempo":
                    events.append((absolute, msg.tempo))
        events.sort(key=lambda x: x[0])
        return events

    def extract_midi_notes(self, midi, track_index=None):
        if track_index is None:
            tracks = enumerate(midi.tracks)
        else:
            if track_index >= len(midi.tracks):
                return []
            tracks = [(track_index, midi.tracks[track_index])]

        all_notes = []

        for _, track in tracks:
            absolute = 0
            active = {}

            for msg in track:
                absolute += msg.time

                if (
                    msg.type == "note_on"
                    and msg.velocity > 0
                ):
                    active.setdefault(msg.note, []).append(
                        (absolute, msg.velocity)
                    )

                elif (
                    msg.type == "note_off"
                    or (
                        msg.type == "note_on"
                        and msg.velocity == 0
                    )
                ):
                    if (
                        msg.note in active
                        and active[msg.note]
                    ):
                        start, velocity = active[msg.note].pop(0)

                        if absolute > start:
                            all_notes.append({
                                "pitch": msg.note,
                                "start_tick": start,
                                "end_tick": absolute,
                                "velocity": msg.velocity or velocity
                            })

        return all_notes

    # ---------------- Visualiser ----------------

    def visualiser_page(self):
        toolbar = tk.Frame(self.content, bg=self.bg)
        toolbar.pack(fill="x", pady=(0, 10))

        self.button(
            toolbar, "Open MIDI", self.open_midi
        ).pack(side="left")

        tk.Label(
            toolbar,
            text="Track",
            bg=self.bg,
            fg=self.muted,
            font=("Segoe UI", 9)
        ).pack(side="left", padx=(18, 6))

        self.visual_track = ttk.Combobox(
            toolbar,
            state="readonly",
            width=28
        )
        self.visual_track.pack(side="left")
        self.visual_track.bind(
            "<<ComboboxSelected>>",
            self.change_visual_track
        )

        self.button(
            toolbar, "−", self.zoom_out, primary=False
        ).pack(side="left", padx=(12, 4))

        self.button(
            toolbar, "+", self.zoom_in, primary=False
        ).pack(side="left")

        self.visual_info = tk.Label(
            toolbar,
            text="No MIDI loaded",
            bg=self.bg,
            fg=self.muted,
            font=("Segoe UI", 9)
        )
        self.visual_info.pack(side="right")

        area = tk.Frame(
            self.content,
            bg=self.panel,
            highlightbackground=self.border,
            highlightthickness=1
        )
        area.pack(fill="both", expand=True)

        self.visual_canvas = tk.Canvas(
            area,
            bg="#111319",
            highlightthickness=0
        )
        self.visual_x = tk.Scrollbar(
            area,
            orient="horizontal",
            command=self.visual_canvas.xview
        )
        self.visual_y = tk.Scrollbar(
            area,
            orient="vertical",
            command=self.visual_canvas.yview
        )

        self.visual_canvas.configure(
            xscrollcommand=self.visual_x.set,
            yscrollcommand=self.visual_y.set
        )

        self.visual_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )
        self.visual_y.pack(side="right", fill="y")
        self.visual_x.pack(side="bottom", fill="x")

        self.visual_canvas.bind(
            "<Button-1>",
            self.click_visualiser
        )

        if self.current_midi:
            self.update_visual_tracks()
            self.draw_piano_roll()
        else:
            self.visual_canvas.create_text(
                500,
                250,
                text="Open a MIDI file to see it here",
                fill=self.muted,
                font=("Segoe UI", 15)
            )

    def update_visual_tracks(self):
        if not self.current_midi:
            return

        values = []

        for index, track in enumerate(
            self.current_midi.tracks
        ):
            name = f"Track {index + 1}"

            for message in track:
                if message.type == "track_name":
                    name = message.name
                    break

            values.append(
                f"{index + 1}: {name}"
            )

        self.visual_track["values"] = values

        if values:
            self.visual_track.current(
                min(self.current_track, len(values) - 1)
            )

    def change_visual_track(self, event=None):
        value = self.visual_track.get()

        if not value:
            return

        try:
            self.current_track = int(
                value.split(":")[0]
            ) - 1
        except ValueError:
            return

        self.draw_piano_roll()

    def zoom_in(self):
        self.visual_zoom = min(
            5,
            self.visual_zoom * 1.25
        )
        self.draw_piano_roll()

    def zoom_out(self):
        self.visual_zoom = max(
            0.2,
            self.visual_zoom / 1.25
        )
        self.draw_piano_roll()

    def tick_to_seconds(self, tick):
        if not self.current_midi:
            return 0

        ticks_per_beat = self.current_midi.ticks_per_beat
        tempo_events = self.get_tempo_events(
            self.current_midi
        )

        if not tempo_events:
            return (
                tick / ticks_per_beat
                * (60 / 120)
            )

        total_seconds = 0
        previous_tick = 0
        current_tempo = 500000

        for event_tick, tempo in tempo_events:
            if event_tick > tick:
                break

            delta_ticks = event_tick - previous_tick

            total_seconds += mido.tick2second(
                delta_ticks,
                ticks_per_beat,
                current_tempo
            )

            previous_tick = event_tick
            current_tempo = tempo

        remaining = tick - previous_tick

        total_seconds += mido.tick2second(
            remaining,
            ticks_per_beat,
            current_tempo
        )

        return total_seconds

    def draw_piano_roll(self):
        if not hasattr(self, "visual_canvas"):
            return

        canvas = self.visual_canvas
        canvas.delete("all")

        if not self.current_midi:
            return

        notes = self.extract_midi_notes(
            self.current_midi,
            self.current_track
        )

        if not notes:
            canvas.create_text(
                500,
                250,
                text="There are no notes in this track.",
                fill=self.muted,
                font=("Segoe UI", 15)
            )
            return

        min_pitch = max(
            0,
            min(note["pitch"] for note in notes) - 3
        )
        max_pitch = min(
            127,
            max(note["pitch"] for note in notes) + 3
        )

        row_height = 22
        left_margin = 58
        time_scale = 120 * self.visual_zoom

        max_seconds = max(
            self.tick_to_seconds(note["end_tick"])
            for note in notes
        )

        width = max(
            1000,
            int(left_margin + max_seconds * time_scale + 100)
        )

        height = (
            (max_pitch - min_pitch + 1)
            * row_height
            + 70
        )

        for pitch in range(min_pitch, max_pitch + 1):
            y = (
                40
                + (max_pitch - pitch)
                * row_height
            )

            note_name = self.midi_note_name(pitch)
            black = note_name.startswith(
                ("C#", "D#", "F#", "G#", "A#")
            )

            canvas.create_rectangle(
                0,
                y,
                width,
                y + row_height,
                fill="#171a20" if black else "#13161b",
                outline="#282d36"
            )

            canvas.create_text(
                30,
                y + row_height / 2,
                text=note_name,
                fill=self.muted,
                font=("Segoe UI", 8)
            )

        step = 0.5
        time = 0

        while time <= max_seconds + step:
            x = left_margin + time * time_scale

            canvas.create_line(
                x, 35, x, height,
                fill="#303641"
            )

            canvas.create_text(
                x + 3,
                15,
                text=f"{time:.1f}s",
                anchor="w",
                fill=self.muted,
                font=("Segoe UI", 8)
            )

            time += step

        for note in notes:
            start = self.tick_to_seconds(
                note["start_tick"]
            )
            end = self.tick_to_seconds(
                note["end_tick"]
            )

            x1 = left_margin + start * time_scale
            x2 = max(
                x1 + 5,
                left_margin + end * time_scale
            )

            y = (
                40
                + (max_pitch - note["pitch"])
                * row_height
            )

            canvas.create_rectangle(
                x1,
                y + 3,
                x2,
                y + row_height - 3,
                fill=self.accent,
                outline="#8b86ff"
            )

        canvas.configure(
            scrollregion=(0, 0, width, height)
        )

        self.visual_info.configure(
            text=(
                f"{len(notes)} notes   "
                f"{max_seconds:.1f}s   "
                f"{self.visual_zoom:.1f}x"
            )
        )

    def click_visualiser(self, event):
        if not self.current_midi:
            return

        x = self.visual_canvas.canvasx(event.x)
        y = self.visual_canvas.canvasy(event.y)

        notes = self.extract_midi_notes(
            self.current_midi,
            self.current_track
        )

        if not notes:
            return

        min_pitch = max(
            0,
            min(note["pitch"] for note in notes) - 3
        )
        max_pitch = min(
            127,
            max(note["pitch"] for note in notes) + 3
        )

        pitch = max_pitch - int(
            (y - 40) / 22
        )

        seconds = max(
            0,
            (x - 58)
            / (120 * self.visual_zoom)
        )

        if 0 <= pitch <= 127:
            self.status_text(
                f"{self.midi_note_name(pitch)} at {seconds:.2f}s"
            )

    # ---------------- Practice ----------------

    def practice_page(self):
        controls = tk.Frame(
            self.content,
            bg=self.bg
        )
        controls.pack(fill="x", pady=(0, 12))

        self.button(
            controls,
            "Load Recording",
            self.load_practice_audio
        ).pack(side="left")

        self.button(
            controls,
            "Record 10 Seconds",
            self.record_practice,
            primary=False
        ).pack(side="left", padx=10)

        self.button(
            controls,
            "Use Current MIDI",
            self.use_current_midi_reference,
            primary=False
        ).pack(side="left")

        self.practice_file_label = tk.Label(
            controls,
            text="No recording loaded",
            bg=self.bg,
            fg=self.muted,
            font=("Segoe UI", 9)
        )
        self.practice_file_label.pack(side="left", padx=12)

        stats = tk.Frame(
            self.content,
            bg=self.bg
        )
        stats.pack(fill="x", pady=(0, 12))

        self.practice_stats = {}

        for title, key in [
            ("Score", "score"),
            ("Timing", "timing"),
            ("Pitch", "pitch"),
            ("BPM", "bpm"),
            ("Duration", "duration")
        ]:
            frame = self.card(stats)
            frame.pack(
                side="left",
                fill="both",
                expand=True,
                padx=4
            )

            tk.Label(
                frame,
                text=title,
                bg=self.panel,
                fg=self.muted,
                font=("Segoe UI", 9)
            ).pack(
                anchor="w",
                padx=13,
                pady=(10, 0)
            )

            label = tk.Label(
                frame,
                text="—",
                bg=self.panel,
                fg=self.text,
                font=("Segoe UI", 18, "bold")
            )
            label.pack(
                anchor="w",
                padx=13,
                pady=(2, 10)
            )

            self.practice_stats[key] = label

        lower = tk.Frame(
            self.content,
            bg=self.bg
        )
        lower.pack(fill="both", expand=True)

        waveform_card = self.card(lower)
        waveform_card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 6)
        )

        tk.Label(
            waveform_card,
            text="Recording",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 13, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 8)
        )

        self.waveform = tk.Canvas(
            waveform_card,
            bg="#111319",
            highlightthickness=0
        )
        self.waveform.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )
        self.waveform.bind(
            "<Configure>",
            lambda event: self.draw_waveform()
        )

        results_card = self.card(lower)
        results_card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(6, 0)
        )

        tk.Label(
            results_card,
            text="Performance",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 13, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 8)
        )

        self.practice_result = tk.Text(
            results_card,
            bg="#15181e",
            fg=self.text,
            insertbackground=self.text,
            relief="flat",
            bd=0,
            wrap="word",
            font=("Segoe UI", 10)
        )
        self.practice_result.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

        self.set_practice_message()

    def set_practice_message(self):
        if not hasattr(self, "practice_result"):
            return

        self.practice_result.delete("1.0", tk.END)
        self.practice_result.insert(
            tk.END,
            "Load a recording and a reference MIDI.\n\n"
            "The analyser will estimate:\n"
            "• overall score\n"
            "• timing accuracy\n"
            "• pitch accuracy\n"
            "• tempo\n"
            "• duration\n\n"
            "The pitch/timing results are estimates from the audio, "
            "so they work best with a clear solo recording."
        )

    def load_practice_audio(self):
        path = filedialog.askopenfilename(
            title="Open Practice Recording",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.ogg"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:
            audio, sr = librosa.load(
                path,
                sr=self.practice_sr,
                mono=True
            )

            self.practice_audio = audio
            self.practice_sr = sr
            self.practice_path = path

            self.practice_file_label.configure(
                text=os.path.basename(path)
            )

            self.analyse_practice()

        except Exception as error:
            messagebox.showerror(
                "Audio Error",
                f"Could not load this recording.\n\n{error}"
            )

    def use_current_midi_reference(self):
        if not self.current_midi:
            path = filedialog.askopenfilename(
                title="Choose Reference MIDI",
                filetypes=[
                    ("MIDI files", "*.mid *.midi")
                ]
            )

            if not path:
                return

            try:
                midi = mido.MidiFile(path)
            except Exception as error:
                messagebox.showerror(
                    "MIDI Error",
                    str(error)
                )
                return
        else:
            midi = self.current_midi
            path = self.current_midi_path

        self.practice_reference = midi

        if path:
            self.status_text(
                f"Reference MIDI: {os.path.basename(path)}"
            )

        self.analyse_practice()

    def record_practice(self):
        seconds = 10
        sample_rate = 44100

        def worker():
            try:
                self.root.after(
                    0,
                    lambda: self.status_text(
                        "Recording for 10 seconds..."
                    )
                )

                recording = sd.rec(
                    int(seconds * sample_rate),
                    samplerate=sample_rate,
                    channels=1,
                    dtype="float32"
                )

                sd.wait()

                recording = recording.flatten()

                path = os.path.join(
                    os.getcwd(),
                    "practice_recording.wav"
                )

                self.save_wav(
                    path,
                    recording,
                    sample_rate
                )

                self.root.after(
                    0,
                    lambda: self.finish_recording(
                        recording,
                        sample_rate,
                        path
                    )
                )

            except Exception as error:
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Recording Error",
                        f"Could not record audio.\n\n{error}"
                    )
                )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def save_wav(self, path, audio, sample_rate):
        audio = np.clip(audio, -1, 1)
        pcm = (audio * 32767).astype(np.int16)

        with wave.open(path, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            output.writeframes(pcm.tobytes())

    def finish_recording(self, audio, sample_rate, path):
        self.practice_audio = audio
        self.practice_sr = sample_rate
        self.practice_path = path

        self.practice_file_label.configure(
            text=os.path.basename(path)
        )

        self.analyse_practice()

    def analyse_practice(self):
        if self.practice_audio is None:
            return

        audio = self.practice_audio
        sr = self.practice_sr

        duration = len(audio) / sr

        try:
            tempo, beat_frames = librosa.beat.beat_track(
                y=audio,
                sr=sr
            )
            bpm = float(
                np.asarray(tempo).reshape(-1)[0]
            )
        except Exception:
            bpm = 0
            beat_frames = np.array([])

        timing_score = None
        pitch_score = None

        if self.practice_reference:
            reference_notes = self.get_reference_seconds()

            if reference_notes:
                detected_notes = self.detect_audio_notes(
                    audio,
                    sr
                )

                timing_score = self.compare_timing(
                    reference_notes,
                    detected_notes
                )

                pitch_score = self.compare_pitch(
                    reference_notes,
                    detected_notes
                )

        if timing_score is None:
            timing_score = self.simple_beat_consistency(
                beat_frames
            )

        if pitch_score is None:
            pitch_score = self.pitch_stability(
                audio,
                sr
            )

        score = (
            timing_score * 0.55
            + pitch_score * 0.45
        )

        self.practice_stats["score"].configure(
            text=f"{score:.0f}%"
        )
        self.practice_stats["timing"].configure(
            text=f"{timing_score:.0f}%"
        )
        self.practice_stats["pitch"].configure(
            text=f"{pitch_score:.0f}%"
        )
        self.practice_stats["bpm"].configure(
            text=f"{bpm:.1f}"
        )
        self.practice_stats["duration"].configure(
            text=self.format_duration(duration)
        )

        self.practice_result.delete(
            "1.0",
            tk.END
        )

        self.practice_result.insert(
            tk.END,
            f"Overall score: {score:.0f}%\n\n"
            f"Timing accuracy: {timing_score:.0f}%\n"
            f"Pitch accuracy: {pitch_score:.0f}%\n"
            f"Detected tempo: {bpm:.1f} BPM\n"
            f"Recording length: {self.format_duration(duration)}\n\n"
        )

        if self.practice_reference:
            self.practice_result.insert(
                tk.END,
                "Reference comparison was used.\n"
                "Timing is based on detected note/onset positions, "
                "and pitch is based on estimated audio pitch."
            )
        else:
            self.practice_result.insert(
                tk.END,
                "No reference MIDI was selected.\n"
                "The timing and pitch figures are general estimates, "
                "rather than a note-by-note comparison."
            )

        self.draw_waveform()
        self.status_text("Practice analysis complete")

    def get_reference_seconds(self):
        if not self.practice_reference:
            return []

        notes = self.extract_midi_notes(
            self.practice_reference
        )

        return [
            {
                "pitch": note["pitch"],
                "start": self.tick_to_seconds_for_midi(
                    self.practice_reference,
                    note["start_tick"]
                ),
                "end": self.tick_to_seconds_for_midi(
                    self.practice_reference,
                    note["end_tick"]
                )
            }
            for note in notes
        ]

    def tick_to_seconds_for_midi(self, midi, tick):
        ticks_per_beat = midi.ticks_per_beat
        tempo_events = self.get_tempo_events(midi)

        if not tempo_events:
            return mido.tick2second(
                tick,
                ticks_per_beat,
                500000
            )

        total = 0
        last_tick = 0
        tempo = 500000

        for event_tick, event_tempo in tempo_events:
            if event_tick > tick:
                break

            total += mido.tick2second(
                event_tick - last_tick,
                ticks_per_beat,
                tempo
            )

            last_tick = event_tick
            tempo = event_tempo

        total += mido.tick2second(
            tick - last_tick,
            ticks_per_beat,
            tempo
        )

        return total

    def detect_audio_notes(self, audio, sr):
        try:
            f0, _, _ = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
                sr=sr,
                frame_length=2048,
                hop_length=256
            )
        except Exception:
            return []

        onsets = librosa.onset.onset_detect(
            y=audio,
            sr=sr,
            units="time",
            backtrack=False
        )

        if len(onsets) == 0:
            return []

        times = librosa.frames_to_time(
            np.arange(len(f0)),
            sr=sr,
            hop_length=256
        )

        midi_values = np.full(
            len(f0),
            np.nan
        )

        valid = np.isfinite(f0)

        midi_values[valid] = (
            librosa.hz_to_midi(
                f0[valid]
            )
        )

        notes = []

        for i, start in enumerate(onsets):
            end = (
                onsets[i + 1]
                if i + 1 < len(onsets)
                else times[-1]
            )

            mask = (
                (times >= start)
                & (times < end)
                & np.isfinite(midi_values)
            )

            values = midi_values[mask]

            if len(values) < 2:
                continue

            pitch = int(
                round(float(np.median(values)))
            )

            notes.append({
                "pitch": pitch,
                "start": float(start),
                "end": float(end)
            })

        return notes

    def compare_timing(self, reference, detected):
        if not reference or not detected:
            return 0

        available = set()
        errors = []

        for i, ref in enumerate(reference):
            best_index = None
            best_error = None

            for j, found in enumerate(detected):
                if j in available:
                    continue

                error = abs(
                    ref["start"] - found["start"]
                )

                if (
                    best_error is None
                    or error < best_error
                ):
                    best_error = error
                    best_index = j

            if best_index is not None:
                available.add(best_index)
                errors.append(best_error)

        if not errors:
            return 0

        mean_error = float(
            np.mean(errors)
        )

        return max(
            0,
            min(
                100,
                100 * math.exp(
                    -mean_error * 4
                )
            )
        )

    def compare_pitch(self, reference, detected):
        if not reference or not detected:
            return 0

        used = set()
        correct = 0

        for ref in reference:
            best_index = None
            best_distance = None

            for j, found in enumerate(detected):
                if j in used:
                    continue

                distance = abs(
                    ref["start"] - found["start"]
                )

                if distance <= 0.5 and (
                    best_distance is None
                    or distance < best_distance
                ):
                    best_distance = distance
                    best_index = j

            if best_index is not None:
                used.add(best_index)

                pitch_error = abs(
                    ref["pitch"]
                    - detected[best_index]["pitch"]
                )

                if pitch_error <= 0.5:
                    correct += 1
                elif pitch_error <= 1.5:
                    correct += 0.5

        return min(
            100,
            (correct / len(reference)) * 100
        )

    def simple_beat_consistency(self, beat_frames):
        if len(beat_frames) < 3:
            return 50

        differences = np.diff(beat_frames)

        if np.mean(differences) <= 0:
            return 50

        variation = (
            np.std(differences)
            / np.mean(differences)
        )

        return max(
            0,
            min(
                100,
                100 - variation * 100
            )
        )

    def pitch_stability(self, audio, sr):
        try:
            f0, _, _ = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
                sr=sr
            )
        except Exception:
            return 50

        valid = f0[np.isfinite(f0)]

        if len(valid) < 10:
            return 50

        midi = librosa.hz_to_midi(valid)
        deviation = np.std(
            midi - np.median(midi)
        )

        return max(
            0,
            min(
                100,
                100 - deviation * 12
            )
        )

    def draw_waveform(self):
        if not hasattr(self, "waveform"):
            return

        canvas = self.waveform
        canvas.delete("all")

        if self.practice_audio is None:
            canvas.create_text(
                350,
                150,
                text="Load or record a performance",
                fill=self.muted,
                font=("Segoe UI", 14)
            )
            return

        audio = self.practice_audio
        width = max(canvas.winfo_width(), 400)
        height = max(canvas.winfo_height(), 220)

        points = min(
            len(audio),
            1600
        )

        indices = np.linspace(
            0,
            len(audio) - 1,
            points
        ).astype(int)

        samples = audio[indices]
        maximum = max(
            np.max(np.abs(samples)),
            0.001
        )

        centre = height / 2
        coords = []

        for i, sample in enumerate(samples):
            x = (
                i
                * width
                / max(1, len(samples) - 1)
            )

            y = centre - (
                sample / maximum
            ) * height * 0.4

            coords.extend(
                [x, y]
            )

        if len(coords) >= 4:
            canvas.create_line(
                *coords,
                fill=self.accent,
                width=2
            )

        canvas.create_line(
            0,
            centre,
            width,
            centre,
            fill="#303641"
        )

    # ---------------- Chords ----------------

    def chords_page(self):
        controls = self.card(self.content)
        controls.pack(fill="x", pady=(0, 15))

        row = tk.Frame(
            controls,
            bg=self.panel
        )
        row.pack(
            fill="x",
            padx=18,
            pady=18
        )

        tk.Label(
            row,
            text="Key",
            bg=self.panel,
            fg=self.muted,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        self.chord_key = ttk.Combobox(
            row,
            values=[
                "C", "C#", "D", "D#", "E", "F",
                "F#", "G", "G#", "A", "A#", "B"
            ],
            state="readonly",
            width=8
        )
        self.chord_key.set("C")
        self.chord_key.pack(
            side="left",
            padx=(8, 18)
        )

        tk.Label(
            row,
            text="Mode",
            bg=self.panel,
            fg=self.muted,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        self.chord_mode = ttk.Combobox(
            row,
            values=["Major", "Minor"],
            state="readonly",
            width=10
        )
        self.chord_mode.set("Major")
        self.chord_mode.pack(
            side="left",
            padx=(8, 18)
        )

        self.button(
            row,
            "Generate",
            self.generate_chords
        ).pack(side="left")

        self.button(
            row,
            "Clear",
            self.clear_progression,
            primary=False
        ).pack(side="left", padx=8)

        middle = tk.Frame(
            self.content,
            bg=self.bg
        )
        middle.pack(fill="both", expand=True)

        left = self.card(middle)
        left.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 6)
        )

        tk.Label(
            left,
            text="Available chords",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 13, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 8)
        )

        self.chord_listbox = tk.Listbox(
            left,
            bg=self.panel,
            fg=self.text,
            selectbackground=self.accent,
            selectforeground=self.text,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Consolas", 11)
        )
        self.chord_listbox.pack(
            fill="both",
            expand=True,
            padx=18
        )

        self.chord_listbox.bind(
            "<Double-Button-1>",
            lambda event: self.add_chord()
        )

        self.button(
            left,
            "Add Selected",
            self.add_chord
        ).pack(
            anchor="w",
            padx=18,
            pady=15
        )

        right = self.card(middle)
        right.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(6, 0)
        )

        tk.Label(
            right,
            text="Progression",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 13, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 8)
        )

        self.progression = tk.Listbox(
            right,
            bg="#15181e",
            fg=self.text,
            selectbackground=self.accent,
            selectforeground=self.text,
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI", 13)
        )
        self.progression.pack(
            fill="both",
            expand=True,
            padx=18
        )

        buttons = tk.Frame(
            right,
            bg=self.panel
        )
        buttons.pack(
            fill="x",
            padx=18,
            pady=15
        )

        self.button(
            buttons,
            "Remove",
            self.remove_chord,
            primary=False
        ).pack(side="left")

        self.button(
            buttons,
            "Export MIDI",
            self.export_chords
        ).pack(side="right")

        self.generate_chords()

    def chord_sets(self):
        major = {
            "C": ["C", "Dm", "Em", "F", "G", "Am", "Bdim"],
            "C#": ["C#", "D#m", "Fm", "F#", "G#", "A#m", "Cdim"],
            "D": ["D", "Em", "F#m", "G", "A", "Bm", "C#dim"],
            "D#": ["D#", "Fm", "Gm", "G#", "A#", "Cm", "Ddim"],
            "E": ["E", "F#m", "G#m", "A", "B", "C#m", "D#dim"],
            "F": ["F", "Gm", "Am", "Bb", "C", "Dm", "Edim"],
            "F#": ["F#", "G#m", "A#m", "B", "C#", "D#m", "Fdim"],
            "G": ["G", "Am", "Bm", "C", "D", "Em", "F#dim"],
            "G#": ["G#", "A#m", "Cm", "C#", "D#", "Fm", "Gdim"],
            "A": ["A", "Bm", "C#m", "D", "E", "F#m", "G#dim"],
            "A#": ["A#", "Cm", "Dm", "D#", "F", "Gm", "Adim"],
            "B": ["B", "C#m", "D#m", "E", "F#", "G#m", "A#dim"]
        }

        minor = {
            "C": ["Cm", "Ddim", "Eb", "Fm", "Gm", "Ab", "Bb"],
            "C#": ["C#m", "D#dim", "E", "F#m", "G#m", "A", "B"],
            "D": ["Dm", "Edim", "F", "Gm", "Am", "Bb", "C"],
            "D#": ["D#m", "Fdim", "F#", "G#m", "A#m", "B", "C#"],
            "E": ["Em", "F#dim", "G", "Am", "Bm", "C", "D"],
            "F": ["Fm", "Gdim", "Ab", "Bbm", "Cm", "Db", "Eb"],
            "F#": ["F#m", "G#dim", "A", "Bm", "C#m", "D", "E"],
            "G": ["Gm", "Adim", "Bb", "Cm", "Dm", "Eb", "F"],
            "G#": ["G#m", "A#dim", "B", "C#m", "D#m", "E", "F#"],
            "A": ["Am", "Bdim", "C", "Dm", "Em", "F", "G"],
            "A#": ["A#m", "Cdim", "C#", "D#m", "Fm", "F#", "G#"],
            "B": ["Bm", "C#dim", "D", "Em", "F#m", "G", "A"]
        }

        return (
            minor
            if self.chord_mode.get() == "Minor"
            else major
        )

    def generate_chords(self):
        chords = self.chord_sets()[
            self.chord_key.get()
        ]

        self.chord_listbox.delete(
            0,
            tk.END
        )

        degrees = [
            "I", "ii", "iii", "IV", "V", "vi", "vii°"
        ]

        for degree, chord in zip(degrees, chords):
            self.chord_listbox.insert(
                tk.END,
                f"{degree:<5}{chord}"
            )

    def add_chord(self):
        selected = self.chord_listbox.curselection()

        if not selected:
            return

        text = self.chord_listbox.get(
            selected[0]
        )

        self.chord_progression.append(
            text.split()[-1]
        )

        self.refresh_progression()

    def remove_chord(self):
        selected = self.progression.curselection()

        if not selected:
            return

        self.chord_progression.pop(
            selected[0]
        )

        self.refresh_progression()

    def clear_progression(self):
        self.chord_progression.clear()
        self.refresh_progression()

    def refresh_progression(self):
        self.progression.delete(
            0,
            tk.END
        )

        for index, chord in enumerate(
            self.chord_progression,
            1
        ):
            self.progression.insert(
                tk.END,
                f"{index}.   {chord}"
            )

    def export_chords(self):
        if not self.chord_progression:
            messagebox.showinfo(
                "No chords",
                "Add some chords first."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Export chord progression",
            defaultextension=".mid",
            filetypes=[("MIDI files", "*.mid")]
        )

        if not path:
            return

        roots = {
            "C": 0, "C#": 1, "Db": 1, "D": 2,
            "D#": 3, "Eb": 3, "E": 4, "F": 5,
            "F#": 6, "Gb": 6, "G": 7, "G#": 8,
            "Ab": 8, "A": 9, "A#": 10, "Bb": 10,
            "B": 11
        }

        try:
            midi = mido.MidiFile(
                ticks_per_beat=480
            )
            track = mido.MidiTrack()
            midi.tracks.append(track)

            track.append(
                mido.MetaMessage(
                    "set_tempo",
                    tempo=mido.bpm2tempo(100)
                )
            )

            for chord in self.chord_progression:
                root_name = chord

                if chord.endswith("dim"):
                    root_name = chord[:-3]
                    intervals = [0, 3, 6]
                elif chord.endswith("m"):
                    root_name = chord[:-1]
                    intervals = [0, 3, 7]
                else:
                    intervals = [0, 4, 7]

                root = roots.get(
                    root_name,
                    0
                )

                notes = [
                    60 + root + interval
                    for interval in intervals
                ]

                for note in notes:
                    track.append(
                        mido.Message(
                            "note_on",
                            note=note,
                            velocity=80,
                            time=0
                        )
                    )

                for index, note in enumerate(notes):
                    track.append(
                        mido.Message(
                            "note_off",
                            note=note,
                            velocity=0,
                            time=1920 if index == 0 else 0
                        )
                    )

            midi.save(path)

            self.status_text(
                f"Exported {os.path.basename(path)}"
            )

            messagebox.showinfo(
                "Export complete",
                "The chord progression was exported."
            )

        except Exception as error:
            messagebox.showerror(
                "Export error",
                f"Could not export the MIDI file.\n\n{error}"
            )

    def format_duration(self, seconds):
        seconds = max(0, int(seconds))
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes}:{seconds:02d}"


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicLab(root)
    root.mainloop()
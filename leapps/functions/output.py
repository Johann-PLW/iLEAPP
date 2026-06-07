"""Output utilities for report folder setup, GUI logging, and screen log export."""

import sys
from datetime import datetime
from pathlib import Path
from leapps.functions.data_sources.text_files import append_content_to_txt_file

identifiers = {}


class GuiWindow:
    """Holds the GUI window handle when running with the Tkinter interface."""
    window_handle = None  # static variable

    @staticmethod
    def set_progress_bar(n):
        """Set the GUI progress bar value if a window handle is available.
        Args:
            n (int | float): Progress value to display.
        """
        if GuiWindow.window_handle:
            progress_bar = GuiWindow.window_handle.nametowidget("progress_bar_frame.progress_bar")
            progress_bar.config(value=n)


class OutputParameters:
    """Stores shared output paths and initializes report directory structure.

    Class Attributes:
        nl (str): Newline marker used by HTML screen output.
        screen_output_file_path (Path | str): Path to the main screen output log.
    """
    # static parameters
    screen_output_file_path = ""

    def __init__(self, leapp, output_folder, custom_folder_name=None):
        """Create output paths and required subfolders for an iLEAPP report.

        Args:
            leapp (namedtuple): LEAPP application settings.
            output_folder (str | Path): Base folder where the report folder is created.
            custom_folder_name (str | None): Optional explicit report folder name.
        """
        now = datetime.now()
        currenttime = str(now.strftime("%Y-%m-%d_%A_%H%M%S"))
        if custom_folder_name:
            folder_name = custom_folder_name
        else:
            folder_name = f"{leapp.name}_Reports_{currenttime}"
        self.output_folder_base = Path(output_folder).joinpath(folder_name)
        self.data_folder = Path(self.output_folder_base).joinpath("data")
        self.media_folder = Path(self.output_folder_base).joinpath("media")
        self.html_media_folder = Path(self.output_folder_base).joinpath("_HTML", "media")
        OutputParameters.screen_output_file_path = Path(self.output_folder_base).joinpath(
            "_HTML", "_Script_Logs", "Screen_Output.html")
        OutputParameters.screen_output_file_path_devinfo = Path(self.output_folder_base).joinpath(
            "_HTML", "_Script_Logs", "DeviceInfo.html")
        OutputParameters.screen_output_file_path_lava_only = Path(self.output_folder_base).joinpath(
            "_HTML", "_Script_Logs", "Lava_only_artifacts_log.html")

        Path.mkdir(Path(self.output_folder_base).joinpath("_HTML", "_Script_Logs"), parents=True)
        Path.mkdir(self.data_folder)
        Path.mkdir(self.media_folder)
        Path.mkdir(self.html_media_folder)


def redirect_logs_in_gui(log_text):
    """Return a writer function that redirects text to a GUI log widget.

    Args:
        log_text: Tkinter text widget used for log display.

    Returns:
        callable: Function that accepts a string and appends it to the widget.
    """
    def redirect_logs(string):
        """Append text to the GUI log widget and keep it scrolled to the end."""
        log_text.insert("end", string)
        log_text.see("end")
        log_text.update()
    return redirect_logs


def logfunc(message=""):
    """Write a message to GUI log, HTML screen log, and standard output.
    Args:
        message (str): Text to log.
    """
    if GuiWindow.window_handle:
        log_text = GuiWindow.window_handle.nametowidget("logs_frame.log_text")
        sys.stdout.write = redirect_logs_in_gui(log_text)

    if OutputParameters.screen_output_file_path:
        content = message + "<br>\n"
        append_content_to_txt_file(OutputParameters.screen_output_file_path, content)

    print(message)


def logdevinfo(message=""):
    """Write a message to the device info HTML log.
    Args:
        message (str): Text to log.
    """
    content = message + "<br>\n"
    append_content_to_txt_file(OutputParameters.screen_output_file_path_devinfo, content)


def write_device_info():
    """Write device information from identifiers to the device info HTML log.
    Iterates through the identifiers dictionary and formats device information
    into an HTML list structure with categories and sources.
    """
    devinfo_path = OutputParameters.screen_output_file_path_devinfo
    for category, values in identifiers.items():
        append_content_to_txt_file(devinfo_path,
                                   "<b>--- <u>" + category + " </u>---</b><br>\n")
        append_content_to_txt_file(devinfo_path, "<ul>\n")
        for label, data in values.items():
            if isinstance(data, list):
                # Handle multiple values
                append_content_to_txt_file(devinfo_path,
                                           "<li><b>" + label + ":</b><ul>\n")
                for item in data:
                    append_content_to_txt_file(devinfo_path,
                                               f'<li>{item["value"]} <span title="{item["source_file"]}" '
                                               f'style="cursor:help"><i>(Source: {item["artifact"]})</i></span></li>\n')
                append_content_to_txt_file(devinfo_path, "</ul></li>\n")
            else:
                # Handle single value
                append_content_to_txt_file(devinfo_path,
                                           f'<li><b>{label}:</b> {data["value"]} <span title="{data["source_file"]}" '
                                           f'style="cursor:help"><i>(Source: {data["artifact"]})</i></span></li>\n')
        append_content_to_txt_file(devinfo_path, "</ul>\n")

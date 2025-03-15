# ruff: noqa: E402  (= ignore imports not at the top of file)
# noqa: E402 (= ignore imports not at the top of file)
# Un-comment the following lines to enable debugging and start the debugger from the `launch.json` configuration in VSCode.

import debugpy

debugpy.listen(58678)

import mesop as me

from fundus_murag.logging_config import setup_logging

setup_logging()


from fundus_murag.assistant.assistant_factory import AssistantFactory
from fundus_murag.config import load_config
from fundus_murag.data.vector_db import VectorDB
from fundus_murag.ui.components import (
    booting_box_component,
    chat_input_component,
    conversations_display_component,
    examples_row_component,
    model_picker_component,
    page_header_component,
)
from fundus_murag.ui.config import APP_NAME, APP_WIDTH, ROOT_BOX_STYLE, STYLESHEETS
from fundus_murag.ui.model_picker_dialog import model_picker_dialog
from fundus_murag.ui.record_dialog import fundus_record_dialog
from fundus_murag.ui.state import (
    AppState,
    ModelPickerDialogState,
    reset_app_state,
    reset_model_picker_dialog_state,
)

__ASSISTANT_FACTORY__ = AssistantFactory()


default_model = __ASSISTANT_FACTORY__.get_default_model()


def on_start_page_load(e: me.LoadEvent):
    app_state = me.state(AppState)
    mpd_state = me.state(ModelPickerDialogState)
    reset_app_state(app_state)
    reset_model_picker_dialog_state(mpd_state)
    yield
    app_state.current_boot_step = "Loading configuration ..."
    yield
    _ = load_config()
    app_state.current_boot_step = "Getting available models ..."
    yield
    app_state.available_models = __ASSISTANT_FACTORY__.list_available_models()
    app_state.current_boot_step = "Setting up FUNDus data ..."
    yield
    _ = VectorDB()  # to confirm that the data is available
    app_state.finished_booting = True
    app_state.current_boot_step = ""
    yield


@me.page(
    path="/",
    stylesheets=STYLESHEETS,
    on_load=on_start_page_load,
    title=APP_NAME,
)
def start_page():
    model_picker_dialog()
    with me.box(style=ROOT_BOX_STYLE):
        page_header_component()
        with me.box(
            style=me.Style(
                width=f"min({APP_WIDTH}, 100%)",
                background=me.theme_var("surface-container"),
                padding=me.Padding.all(24),
                border_radius="16px",
                margin=me.Margin.symmetric(
                    horizontal="auto",
                    vertical=36,
                ),
            )
        ):
            state = me.state(AppState)
            if not state.finished_booting:
                booting_box_component()
            else:
                me.text(
                    "🔮 Explore the FUNDus! data with the FUNDus! Assistant!",
                    style=me.Style(
                        font_size=20, margin=me.Margin.symmetric(vertical=16)
                    ),
                )
                me.divider()
                me.link(
                    text="Or click here to browse FUNDus! via 🔎 Cross-Modal Semantic Similarity Search!",
                    open_in_new_tab=True,
                    url="https://fundus-ir.ltdemos.informatik.uni-hamburg.de/",
                    style=me.Style(
                        font_size=14,
                        margin=me.Margin.symmetric(vertical=16),
                        text_decoration="none",
                        color=me.theme_var("on-surface"),
                        cursor="pointer",
                    ),
                )
                me.divider()
                me.text(
                    "🚧 This is an early beta Proof-of-Concept version! So be prepared, you will encouter 🐛 🪲 🪳 🐞 🕷️ 🐜",
                    type="subtitle-1",
                    style=me.Style(
                        margin=me.Margin.symmetric(vertical=16),
                    ),
                )
                me.divider()
                model_picker_component()
                examples_row_component()
                chat_input_component()


@me.page(
    path="/conversation",
    stylesheets=STYLESHEETS,
    title=APP_NAME,
)
def conversation_page():
    fundus_record_dialog()
    with me.box(style=ROOT_BOX_STYLE):
        page_header_component()

        with me.box(
            style=me.Style(
                width=f"min({APP_WIDTH}, 100%)",
                height="calc(100vh - 100px)",
                background=me.theme_var("surface-container"),
                overflow_y="auto",
                padding=me.Padding.all(24),
                border_radius="16px",
                margin=me.Margin.symmetric(
                    horizontal="auto",
                    vertical=36,
                ),
            )
        ):
            conversations_display_component()

        with me.box(
            style=me.Style(
                display="flex",
                justify_content="center",
            )
        ):
            with me.box(
                style=me.Style(
                    width=f"min({APP_WIDTH}, 100%)",
                    margin=me.Margin(top=5, bottom=5),
                )
            ):
                chat_input_component()

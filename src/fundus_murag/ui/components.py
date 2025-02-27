import mesop as me

from fundus_murag.assistant.dto import ChatMessage

# from fundus_murag.assistant.gemini_fundus_assistant import GeminiFundusAssistant
from fundus_murag.data.dto import FundusCollection, FundusRecordInternal
from fundus_murag.data.vector_db import VectorDB
from fundus_murag.ui.config import APP_NAME, EXAMPLES
from fundus_murag.ui.state import AppState, reset_app_state
from fundus_murag.ui.utils import (
    contains_fundus_collection_render_tag,
    contains_fundus_record_render_tag,
    extract_murag_id_from_fundus_collection_render_tags,
    extract_murag_id_from_fundus_record_render_tags,
    get_assistant_instance,
    replace_fundus_collection_render_tag,
    replace_fundus_record_render_tag,
)

__VDB__ = VectorDB()


def booting_box_component():
    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="row",
            align_items="center",
            justify_content="center",
            margin=me.Margin.symmetric(vertical="100"),
            width="100%",
        )
    ):
        state = me.state(AppState)
        me.text(
            f"Booting FUNDus Assistant: {state.current_boot_step}",
            type="headline-5",
        )


def examples_row_component():
    me.text(
        "Try one of these examples or type your own question:",
        style=me.Style(
            font_weight=500,
            font_style="italic",
            margin=me.Margin(bottom=16),
        ),
    )
    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="row",
            gap=16,
            margin=me.Margin(bottom=24),
            align_items="stretch",
            justify_content="space-between",
        )
    ):
        for ex in EXAMPLES:
            example_box_component(ex)


def example_box_component(text: str):
    def on_click(e: me.ClickEvent):
        state = me.state(AppState)
        state.current_user_input = e.key

    with me.tooltip(
        message="Click to use this example",
        position_at_origin=True,
        position="below",
    ):
        with me.box(
            key=text,
            on_click=on_click,
            style=me.Style(
                background=me.theme_var("primary-container"),
                color=me.theme_var("on-primary-container"),
                cursor="pointer",
                width="175px",
                height="100px",
                font_weight=500,
                line_height="1.5",
                padding=me.Padding.all(8),
                border_radius=16,
                border=me.Border.all(
                    me.BorderSide(
                        width=1,
                        color="on-primary-fixed",
                        style="solid",
                    )
                ),
            ),
        ):
            me.text(text)


def page_header_component():
    def on_click(e: me.ClickEvent):
        reset_app_state(me.state(AppState))
        me.navigate("/")

    def toggle_theme(e: me.ClickEvent):
        if me.theme_brightness() == "light":
            me.set_theme_mode("dark")
        else:
            me.set_theme_mode("light")

    with me.box(
        on_click=on_click,
        style=me.Style(
            padding=me.Padding.all(16),
            display="flex",
            flex_direction="row",
            justify_content="space-between",
        ),
    ):
        with me.tooltip(
            message="Navigate back to the main page. This resets the chat session.",
            position="below",
        ):
            me.text(
                APP_NAME,
                style=me.Style(
                    cursor="pointer",
                    font_weight=500,
                    font_size=30,
                    color=me.theme_var("on-surface-variant"),
                    letter_spacing="0.3px",
                ),
            )

        with me.tooltip(
            message=f"Switch theme to {'light mode' if me.theme_brightness() == 'dark' else 'dark mode'}",
            position="below",
        ):
            with me.content_button(
                type="icon",
                style=me.Style(
                    margin=me.Margin(left="auto"),
                ),
                on_click=toggle_theme,
            ):
                me.icon(
                    "light_mode" if me.theme_brightness() == "dark" else "dark_mode",
                )


def submit_input_textarea():
    state = me.state(AppState)
    current_user_input = state.current_user_input.strip()
    if current_user_input != "":
        assistant = get_assistant_instance(state.selected_model, state.available_models)
        if not assistant.get_chat_messages() or len(assistant.get_chat_messages()) == 0:
            me.navigate("/conversation")
        assistant.send_text_message(
            prompt=current_user_input,
            reset_chat=False,
        )

        me.scroll_into_view(key="end_of_messages")


def on_chat_send_button_click(e: me.ClickEvent):
    state = me.state(AppState)
    submit_input_textarea()
    yield
    state.current_user_input = ""
    yield


def on_chat_reset_button_click(e: me.ClickEvent):
    state = me.state(AppState)
    reset_app_state(state)
    yield
    me.navigate("/")
    yield


def on_input_textarea_blur(e: me.InputBlurEvent):
    state = me.state(AppState)
    state.current_user_input = e.value
    yield
    submit_input_textarea()
    yield
    state.current_user_input = ""
    yield


def on_input_textarea_submit(e: me.TextareaShortcutEvent):
    state = me.state(AppState)
    state.current_user_input = e.value
    yield
    submit_input_textarea()
    yield
    state.current_user_input = ""
    yield


def on_input_textarea_newline(e: me.TextareaShortcutEvent):
    state = me.state(AppState)
    state.current_user_input = e.value + "\n"
    yield


def on_input_textarea_clear(e: me.TextareaShortcutEvent):
    state = me.state(AppState)
    state.current_user_input = ""
    yield


def chat_input_component():
    with me.box(
        style=me.Style(
            border_radius=16,
            padding=me.Padding.all(8),
            background=me.theme_var("surface-container-highest"),
            display="flex",
            width="100%",
        )
    ):
        state = me.state(AppState)
        with me.box(style=me.Style(flex_grow=1)):
            me.native_textarea(
                value=state.current_user_input,
                placeholder="Enter a question",
                # on_blur=on_input_textarea_blur,
                shortcuts={
                    me.Shortcut(key="Enter"): on_input_textarea_submit,
                    me.Shortcut(shift=True, key="Enter"): on_input_textarea_newline,
                    me.Shortcut(key="Escape"): on_input_textarea_clear,
                },
                disabled=not state.finished_booting or state.selected_model == "",
                style=me.Style(
                    padding=me.Padding.all(10),
                    outline="none",
                    width="100%",
                    height="100%",
                    border=me.Border.all(me.BorderSide(style="none")),
                    border_radius=16,
                ),
                autosize=False,
                min_rows=1,
                max_rows=1,
            )

        with me.tooltip(message="Send your message"):
            with me.content_button(
                type="icon",
                on_click=on_chat_send_button_click,
                disabled=not state.finished_booting
                or state.current_user_input == ""
                or state.selected_model == "",
            ):
                me.icon("send")

        with me.tooltip(message="Start a new conversation"):
            with me.content_button(
                type="icon",
                on_click=on_chat_reset_button_click,
                disabled=not state.finished_booting,
            ):
                me.icon("chat_add_on")


def on_model_picker_click(e: me.ClickEvent):
    state = me.state(AppState)
    state.is_model_picker_dialog_open = True
    yield


def model_picker_component():
    with me.tooltip(message="Click to select a model"):
        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="row",
                gap=16,
                margin=me.Margin.symmetric(vertical=24),
                cursor="alias",
            ),
            on_click=on_model_picker_click,
        ):
            state = me.state(AppState)
            me.text(
                "Selected Model:",
                style=me.Style(
                    font_weight=500,
                    font_style="italic",
                    margin=me.Margin(bottom=16),
                ),
            )
            if state.selected_model != "":
                me.text(
                    state.selected_model_display_name,
                    style=me.Style(
                        font_weight="bold",
                        color=me.theme_var("error"),
                    ),
                )
            else:
                me.text(
                    "⚠️ Please select a model!",
                    style=me.Style(
                        font_weight="bold",
                        color=me.theme_var("error"),
                    ),
                )


def conversations_display_component():
    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            gap=16,
            margin=me.Margin(top=24),
            overflow_y="scroll",
        )
    ):
        state = me.state(AppState)
        assistant = get_assistant_instance(state.selected_model, state.available_models)

        messages = assistant.get_chat_messages()
        if not messages:
            return
        for message in messages:
            display_message(message)
        if len(messages) > 0:
            me.box(
                key="end_of_messages",
            )


def display_message(message: ChatMessage):
    if message.role == "user":
        user_message_component(message.content)
    else:
        model_message_component(message.content)


def user_message_component(content: str):
    with me.box(
        style=me.Style(
            background=me.theme_var("secondary-container"),
            color=me.theme_var("on-secondary-container"),
            padding=me.Padding.all(8),
            border_radius="16px",
            text_align="right",
            width="90%",
            align_self="flex-end",
        )
    ):
        me.text(
            "You",
            style=me.Style(
                font_weight="bold",
                padding=me.Padding(bottom=2),
                text_align="right",
            ),
        )
        me.divider(inset=False)

        me.markdown(
            content,
        )


def model_message_component(content: str):
    with me.box(
        style=me.Style(
            background=me.theme_var("primary-container"),
            color=me.theme_var("on-primary-container"),
            padding=me.Padding.all(8),
            border_radius="16px",
            text_align="left",
            width="90%",
            align_self="flex-start",
        )
    ):
        state = me.state(AppState)
        me.text(
            state.selected_model_display_name,
            style=me.Style(
                font_weight="bold",
                padding=me.Padding(bottom=2),
            ),
        )

        me.divider(inset=False)

        if contains_fundus_record_render_tag(content):
            murag_ids = extract_murag_id_from_fundus_record_render_tags(content)
            if murag_ids is not None:
                content = replace_fundus_record_render_tag(content)
                me.markdown(content)
                records = []
                for murag_id in murag_ids:
                    record = __VDB__.get_fundus_record_internal_by_murag_id(murag_id)
                    records.append(record)
                fundus_records_component(records)
        elif contains_fundus_collection_render_tag(content):
            murag_ids = extract_murag_id_from_fundus_collection_render_tags(content)
            content = replace_fundus_collection_render_tag(content)
            me.markdown(content)
            if murag_ids is not None:
                for murag_id in murag_ids:
                    collection = __VDB__.get_fundus_collection_by_murag_id(murag_id)
                    fundus_collection_component(collection)
        else:
            me.markdown(content)


def fundus_records_component(records: list[FundusRecordInternal]):
    with me.box(
        style=me.Style(
            display="flex",
            flex_wrap="wrap",
            gap=16,
            justify_content="center",
            margin=me.Margin(top=24),
        )
    ):
        for record in records:
            fundus_record_component(record)


def on_fundus_record_click(e: me.ClickEvent):
    state = me.state(AppState)
    state.is_record_dialog_open = True
    state.current_enlarged_record_murag_id = e.key


def fundus_record_component(record: FundusRecordInternal):
    with me.box(
        style=me.Style(
            background=me.theme_var("surface-container-highest"),
            color=me.theme_var("on-surface-variant"),
            padding=me.Padding.all(8),
            border_radius=16,
            border=me.Border.all(me.BorderSide(width=1, color="#e0e0e0")),
            box_shadow="rgba(0, 0, 0, 0.16) 0px 3px 6px, rgba(0, 0, 0, 0.23) 0px 3px 6px;",
            margin=me.Margin.symmetric(vertical=4),
            width="30%",
            cursor="pointer",
        ),
        key=record.murag_id,
        on_click=on_fundus_record_click,
    ):
        md = (
            f"**Title**: _`{record.title}`_\n\n"
            f"**Collection**: _`{record.collection.title}`_\n\n"
            f"**FUNDus! ID**: _`{record.fundus_id}`_\n\n"
            f"**Catalog No.**: _`{record.catalogno}`_\n\n"
        )
        me.markdown(md)
        # render the image centered
        with me.box(
            style=me.Style(
                display="flex",
                justify_content="center",
                align_items="center",
                margin=me.Margin(top=8),
            ),
            key=record.murag_id,
        ):
            with me.tooltip(
                message="Click to enlarge and view details!",
                position_at_origin=True,
                position="below",
            ):
                me.image(
                    src="data:image/png;base64," + record.base64_image,
                    style=me.Style(
                        max_width="200px",
                        max_height="200px",
                        border_radius=16,
                    ),
                )

        me.divider(inset=False)

        me.link(
            text="🔗 View on FUNDus!",
            url=f"https://www.fundus.uni-hamburg.de/de/collection_records/{record.fundus_id}",
            open_in_new_tab=True,
            style=me.Style(
                color=me.theme_var("tertiary"),
                font_style="italic",
                font_size="small",
                text_decoration="none",
                margin=me.Margin(top="auto"),
            ),
        )


def fundus_collection_component(collection: FundusCollection):
    with me.box(
        style=me.Style(
            background=me.theme_var("surface-container-highest"),
            color=me.theme_var("on-surface-variant"),
            padding=me.Padding.all(8),
            border_radius=16,
            border=me.Border.all(me.BorderSide(width=1, color="#e0e0e0")),
            box_shadow="rgba(0, 0, 0, 0.16) 0px 3px 6px, rgba(0, 0, 0, 0.23) 0px 3px 6px;",
            margin=me.Margin.symmetric(vertical=4),
        )
    ):
        md = (
            "**Collection ID**\n"
            f"_{collection.collection_name}_\n\n"
            "**Title**\n"
            f"_{collection.title}_\n\n"
            "**Title (DE)**\n"
            f"_{collection.title_de}_\n\n"
            "**Description**\n"
            f"_{collection.description}_\n\n"
            "**Description (DE)**\n"
            f"_{collection.description_de}_"
        )

        me.markdown(md)

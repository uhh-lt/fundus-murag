import mesop as me

from fundus_murag.ui.config import APP_WIDTH
from fundus_murag.ui.dialog import dialog, dialog_actions
from fundus_murag.ui.state import AppState, ModelPickerDialogState


def on_model_table_click(e: me.TableClickEvent):
    state = me.state(ModelPickerDialogState)
    app_state = me.state(AppState)
    if app_state.available_models is None or len(app_state.available_models) == 0:
        return
    state.selected_model_display_name = str(
        app_state.available_models.iloc[e.row_index]["display_name"]
    )
    state.selected_model = str(app_state.available_models.iloc[e.row_index]["name"])


def model_selection_component():
    me.text(
        "Choose a Model by clicking on the respective row:",
        style=me.Style(
            font_weight=500, font_style="italic", margin=me.Margin(bottom=16)
        ),
    )
    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="row",
            gap=16,
            margin=me.Margin(bottom=24),
        )
    ):
        app_state = me.state(AppState)
        state = me.state(ModelPickerDialogState)
        if app_state.available_models is None or len(app_state.available_models) == 0:
            me.text("No models available.", style=me.Style(color=me.theme_var("error")))
        else:
            with me.box(
                style=me.Style(
                    width=APP_WIDTH,
                    border_radius=4,
                    border=me.Border.all(
                        me.BorderSide(color="lightgray", width=1, style="solid")
                    ),
                    overflow="auto",
                    cursor="pointer",
                )
            ):
                me.table(
                    app_state.available_models,
                    on_click=on_model_table_click,
                    header=me.TableHeader(sticky=True),
                )
    me.text(
        "Selected Model:",
        type="subtitle-1",
        style=me.Style(
            margin=me.Margin(top=16),
            font_weight="bold",
        ),
    )
    me.text(
        state.selected_model_display_name,
        type="subtitle-1",
        style=me.Style(
            margin=me.Margin(top=16),
            color=me.theme_var("error"),
            font_weight="bold",
        ),
    )


def close_model_picker_dialog(e: me.ClickEvent):
    state = me.state(ModelPickerDialogState)
    state.selected_model_display_name = ""
    state.selected_model = ""
    app_state = me.state(AppState)
    app_state.is_model_picker_dialog_open = False


def confirm_model_picker_dialog(e: me.ClickEvent):
    state = me.state(ModelPickerDialogState)
    app_state = me.state(AppState)
    app_state.selected_model = state.selected_model
    app_state.selected_model_display_name = state.selected_model_display_name
    state.selected_model = ""
    state.selected_model_display_name = ""
    app_state.is_model_picker_dialog_open = False


def model_picker_dialog():
    state = me.state(AppState)
    with dialog(state.is_model_picker_dialog_open):
        model_selection_component()
        with dialog_actions():
            me.button(
                "Cancel",
                on_click=close_model_picker_dialog,
                type="stroked",
                style=me.Style(
                    margin=me.Margin(right=16),
                    background=me.theme_var("error"),
                    color=me.theme_var("on-error"),
                ),
            )
            me.button(
                "Confirm",
                on_click=confirm_model_picker_dialog,
                type="flat",
                style=me.Style(
                    background=me.theme_var("primary"),
                    color=me.theme_var("on-primary"),
                ),
            )

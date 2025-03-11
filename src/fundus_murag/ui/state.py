import mesop as me
import pandas as pd

from fundus_murag.ui.utils import get_assistant_instance, get_available_models_df


@me.stateclass
class AppState:
    is_model_picker_dialog_open: bool
    is_record_dialog_open: bool

    finished_booting: bool
    current_boot_step: str

    available_models: pd.DataFrame
    selected_model_display_name: str = "Gemini 2.0 Flash 001"
    selected_model: str = "models/gemini-2.0-flash-001"

    current_user_input: str
    current_enlarged_record_murag_id: str


@me.stateclass
class ModelPickerDialogState:
    selected_model_display_name: str = ""
    selected_model: str = ""


def reset_app_state(state: AppState):
    state.available_models = get_available_models_df()

    state.selected_model_display_name = "Gemini 2.0 Flash 001"
    state.selected_model = "models/gemini-2.0-flash-001"

    assistant = get_assistant_instance(state.selected_model, state.available_models)
    assistant.reset_chat_session()

    state.is_model_picker_dialog_open = False
    state.is_record_dialog_open = False
    state.finished_booting = False
    state.current_boot_step = ""

    state.current_enlarged_record_murag_id = ""
    state.current_user_input = ""


def reset_model_picker_dialog_state(state: ModelPickerDialogState):
    state.selected_model_display_name = ""
    state.selected_model = ""

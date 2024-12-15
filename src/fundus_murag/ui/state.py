import mesop as me
import pandas as pd

from fundus_murag.assistant.gemini_fundus_assistant import GeminiFundusAssistant


@me.stateclass
class AppState:
    is_model_picker_dialog_open: bool
    is_record_dialog_open: bool

    finished_booting: bool
    current_boot_step: str

    available_models: pd.DataFrame
    selected_model_display_name: str = "Gemini 1.5 Flash 002"
    selected_model: str = "gemini-1.5-flash-002"

    current_user_input: str
    current_enlarged_record_murag_id: str


@me.stateclass
class ModelPickerDialogState:
    selected_model_display_name: str = ""
    selected_model: str = ""


def reset_app_state(state: AppState):
    gemini = GeminiFundusAssistant(state.selected_model)
    gemini.reset_chat_session()

    state.is_model_picker_dialog_open = False
    state.is_record_dialog_open = False

    state.finished_booting = False
    state.current_boot_step = ""

    state.available_models = pd.DataFrame()
    state.selected_model_display_name = "Gemini 1.5 Pro 002"
    state.selected_model = "gemini-1.5-pro-002"

    state.current_enlarged_record_murag_id = ""
    state.current_user_input = ""


def reset_model_picker_dialog_state(state: ModelPickerDialogState):
    state.selected_model_display_name = ""
    state.selected_model = ""

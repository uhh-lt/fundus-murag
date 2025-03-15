import mesop as me
import pandas as pd

from fundus_murag.assistant.assistant_factory import AssistantFactory

__ASSISTANT_FACTORY__ = AssistantFactory()

default_model = __ASSISTANT_FACTORY__.get_default_model()


@me.stateclass
class AppState:
    is_model_picker_dialog_open: bool
    is_record_dialog_open: bool

    finished_booting: bool
    current_boot_step: str

    available_models: pd.DataFrame
    selected_model: str
    selected_model_display_name: str

    chat_session_id: str

    current_user_input: str
    current_enlarged_record_murag_id: str


@me.stateclass
class ModelPickerDialogState:
    selected_model_display_name: str = ""
    selected_model: str = ""


def reset_app_state(state: AppState):
    state.is_model_picker_dialog_open = False
    state.is_record_dialog_open = False

    state.finished_booting = False
    state.current_boot_step = ""

    state.available_models = __ASSISTANT_FACTORY__.list_available_models()
    state.selected_model = default_model.name
    state.selected_model_display_name = default_model.display_name

    state.chat_session_id = ""

    state.current_user_input = ""
    state.current_enlarged_record_murag_id = ""


def reset_model_picker_dialog_state(state: ModelPickerDialogState):
    state.selected_model_display_name = ""
    state.selected_model = ""

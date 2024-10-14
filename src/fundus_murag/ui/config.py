import mesop as me

STYLESHEETS = [
    "https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap"
]

ROOT_BOX_STYLE = me.Style(
    background=me.theme_var("background"),
    height="100%",
    font_family="Inter",
    display="flex",
    flex_direction="column",
)

EXAMPLES = [
    "What is FUNDus!?",
    "What functionality do you provide?",
    "What collections are contained in FUNDus?",
    "Show me a random FUNDus! record!",
    # "How many records are in FUNDus!?",
    "Show me an image depicting a greek statue!",
]

APP_NAME = "🔮 FUNDus! Assistant"

APP_WIDTH = "1024px"

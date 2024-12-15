import mesop as me

from fundus_murag.data.vector_db import VectorDB
from fundus_murag.ui.config import APP_WIDTH
from fundus_murag.ui.dialog import dialog, dialog_actions
from fundus_murag.ui.state import AppState


def large_fundus_record_component(murag_id: str | None):
    if murag_id is None or murag_id == "":
        return
    vdb = VectorDB()
    record = vdb.get_fundus_record_internal_by_murag_id(murag_id)

    with me.box(
        style=me.Style(
            background=me.theme_var("surface-container-highest"),
            color=me.theme_var("on-surface-variant"),
            padding=me.Padding.all(8),
            border_radius=16,
            border=me.Border.all(me.BorderSide(width=1, color="#e0e0e0")),
            box_shadow="rgba(0, 0, 0, 0.16) 0px 3px 6px, rgba(0, 0, 0, 0.23) 0px 3px 6px;",
            margin=me.Margin.symmetric(vertical=4),
            width=APP_WIDTH,
        )
    ):
        # two columns: left for metadata, right for image
        with me.box(
            style=me.Style(
                display="flex",
                flex_direction="row",
                gap=4,
            )
        ):
            with me.box(
                style=me.Style(
                    width="50%",
                )
            ):
                md = (
                    f"**Title** `{record.title}`\n\n"
                    f"**Collection** `{record.collection.title}`\n\n"
                    f"**FUNDus! ID** `{record.fundus_id}`\n\n"
                    f"**Catalog No.** `{record.catalogno}`\n\n"
                )
                details_md = (
                    "<details>\n" "<summary>Click to view details</summary>\n\n\n"
                )

                for key, value in record.details.items():
                    details_md += f"**{key}**\n`{value}`\n\n"
                details_md += "</details>"
                md += details_md

                me.markdown(md)

            with me.box(
                style=me.Style(
                    width="50%",
                )
            ):
                # render the image centered
                with me.box(
                    style=me.Style(
                        display="flex",
                        justify_content="center",
                        align_items="center",
                        margin=me.Margin(top=8),
                    )
                ):
                    me.image(
                        src="data:image/png;base64," + record.base64_image,
                        style=me.Style(
                            max_width="100%",
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
                margin=me.Margin(top=16),
            ),
        )


def close_fundus_record_dialog(e: me.ClickEvent):
    state = me.state(AppState)
    state.is_record_dialog_open = False


def fundus_record_dialog():
    state = me.state(AppState)
    with dialog(state.is_record_dialog_open):
        large_fundus_record_component(state.current_enlarged_record_murag_id)
        with dialog_actions():
            me.button(
                "Close",
                on_click=close_fundus_record_dialog,
                type="flat",
                color="primary",
            )

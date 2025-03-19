from fundus_murag.data.dtos.fundus import (
    FundusCollection,
    FundusRecord,
)

FUNDUS_INTRO_EN = """
FUNDus! is the research portal of the University of Hamburg, with which we make the scientific collection objects of the University of Hamburg and the Leibniz-Institute for the Analysis of Biodiversity Change (LIB) generally accessible. In addition werden provide information about the collections of the Staats- and Universitätsbiliothek Hamburg. We want to promote the joy of research! Our thematically arranged offer is therefore aimed at all those who want to use every opportunity for research and discovery with enthusiasm and joy."
There are over 13 million objects in 37 scientific collections at the University of Hamburg and the LIB - from A for anatomy to Z for zoology. Some of the objects are hundreds or even thousands of years old, others were created only a few decades ago."

Since autumn 2018, interesting new collection objects have been regularly published here. In the coming months you can discover many of them for the first time on this portal.

We are very pleased to welcome you here and cordially invite you to continue discovering the interesting, exciting and sometimes even bizarre objects in the future. In the name of all our employees who have implemented this project together, we wish you lots of fun in your research and discovery!
"""

FUNDUS_COLLECTION_DOC_STRING = FundusCollection.__doc__

FUNDUS_ITEM_DOC_STRING = FundusRecord.__doc__

FUNDUS_RECORD_RENDER_TAG_OPEN = "<FundusRecord"
FUNDUS_COLLECTION_RENDER_TAG_OPEN = "<FundusCollection"
RENDER_TAG_MURAG_ID_ATTRIBUTE = "murag_id"
RENDER_TAG_CLOSE = "/>"

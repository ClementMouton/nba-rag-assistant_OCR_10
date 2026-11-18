# MÉTHODOLOGIE — Instrumentation du pipeline
# Les traces aident à observer les étapes de traitement et les erreurs.
# Elles ne constituent pas à elles seules une validation de la qualité
# documentaire, statistique ou factuelle des réponses générées.


import os

import logfire
from dotenv import load_dotenv

load_dotenv()

LOGFIRE_ENABLED = bool(os.getenv("LOGFIRE_TOKEN"))

logfire.configure(
    service_name="nba-rag-assistant",
    send_to_logfire="if-token-present",
    inspect_arguments=False,
)


def trace_step(name: str, **attributes):
    return logfire.span(name, **attributes)

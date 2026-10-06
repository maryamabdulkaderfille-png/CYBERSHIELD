"""Parser for legacy Outlook .msg files (OLE/Compound File Binary Format).

Not implemented yet — real .msg parsing needs a dedicated library (e.g.
`extract-msg`) that isn't a project dependency yet, to keep this phase's
footprint minimal. This module is the integration point for adding that
support later: implement `parse_msg_file` to return an `EmailContext` (see
app.services.email_scanner.types) and swap out the error below — nothing
else in the email scanner needs to change, since the route/service layer
already calls this function for `.msg` uploads.
"""

from app.utils.errors import APIError


def parse_msg_file(content: bytes):
    raise APIError(
        ".msg file parsing is not yet supported in this version. Please export the email as .eml, "
        "or paste its content into the text box instead.",
        422,
    )

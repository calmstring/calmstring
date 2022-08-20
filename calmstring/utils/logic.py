def signals_emiter(
    internal=None,
    external=None,
    emit_signals=True,
    emit_internal_signals=True,
    emit_external_signals=True,
    **kwargs,
):
    """Function that takes internal and external callbacks and calls them.

    Args:
        internal (_type_, optional): _description_. Defaults to None.
        external (_type_, optional): _description_. Defaults to None.
        emit_signals (bool, optional): when False internal and external will not be called. Defaults to True.
        emit_internal_signals (bool, optional): when False internal will not be called. Defaults to True.
        emit_external_signals (bool, optional): when False external will not be called. Defaults to True.

    Returns:
        _type_: _description_
    """

    if not emit_signals:
        return None

    if emit_external_signals and emit_signals and external:
        external()

    if emit_internal_signals and emit_signals and internal:
        internal()
    return True

def classificar_erro(erro):
    if not erro:
        return "desconhecido"

    erro_lower = erro.lower()

    # 🔎 SELECTOR (não encontrou elemento)
    if any(p in erro_lower for p in [
        "element not found",
        "no element found",
        "cannot find",
        "not found",
        "failed to find element"
    ]):
        return "selector"

    # ⏱️ TIMEOUT
    elif any(p in erro_lower for p in [
        "timed out",
        "timeout",
        "waiting for",
        "retrying"
    ]):
        return "timeout"

    # 📏 ASSERTION
    elif any(p in erro_lower for p in [
        "assertionerror",
        "expected",
        "to equal",
        "to contain"
    ]):
        return "assertion"

    # 🖱️ INTERAÇÃO
    elif any(p in erro_lower for p in [
        "not visible",
        "not interactable",
        "cy.click",
        "is being covered",
        "detached from dom"
    ]):
        return "interacao"

    # 🌐 REDE / API (novo)
    elif any(p in erro_lower for p in [
        "network error",
        "failed to fetch",
        "status code",
        "xhr"
    ]):
        return "rede"

    # ⚙️ JS / ERRO FRONT
    elif any(p in erro_lower for p in [
        "uncaught",
        "typeerror",
        "referenceerror"
    ]):
        return "js"

    else:
        return "desconhecido"
from .providers import provider_status


def diagnostics():
    return {
        "brain": "RAKIB 3.0",
        "providers": provider_status(),
        "architecture": {
            "intent_router": "AVAILABLE",
            "memory": "AVAILABLE",
            "web_research": "AVAILABLE",
            "local_tools": "AVAILABLE",
            "answer_engine": "AVAILABLE",
        },
    }

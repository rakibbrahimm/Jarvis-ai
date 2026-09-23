from .intent import detect_intent


class RAKIBRouter:
    """
    RAKIB 3.0 Smart Brain Router

    Decides which brain should handle a request:
      - local tools for deterministic tasks
      - web/core for current information
      - AI providers for general reasoning
      - automatic fallback when a provider fails
    """

    def __init__(self):
        self.providers = []

    def register(self, name, handler, priority=100):
        if callable(handler):
            self.providers.append((priority, name, handler))
            self.providers.sort(key=lambda x: x[0])

    def _ordered_providers(self, command):
        intent = detect_intent(command)

        # Names used by server.py
        local_names = {
            "rakib-core",
            "rakib-tools",
            "rakib-web",
            "rakib-answer-engine",
            "rakib-memory",
        }

        ai_names = {
            "openai",
            "gemini",
            "perplexity",
        }

        local = []
        ai = []
        other = []

        for item in self.providers:
            _, name, _ = item

            if name in local_names:
                local.append(item)
            elif name in ai_names:
                ai.append(item)
            else:
                other.append(item)

        # Deterministic requests should never waste an AI request.
        if intent in {
            "math",
            "time",
            "date",
            "conversion",
        }:
            return local + other + ai

        # Current/news requests need fresh information first.
        if intent == "web":
            return local + ai + other

        # Knowledge/general questions:
        # try real AI first, then local/web fallback.
        if intent in {
            "knowledge",
            "general",
        }:
            return ai + local + other

        return ai + local + other

    def ask(self, command):
        errors = []
        intent = detect_intent(command)

        for _, name, handler in self._ordered_providers(command):
            try:
                result = handler(command)

                if result and str(result).strip():
                    return str(result).strip(), name

            except Exception as error:
                errors.append(f"{name}: {error}")

        # Never pretend an AI provider answered when it didn't.
        if errors:
            return (
                "RAKIB is online, but no connected AI provider returned "
                "an answer. Check the provider configuration or API "
                "availability. Local tools and web fallback remain available.",
                "provider-unavailable",
            )

        return (
            "RAKIB is online, but no AI provider is currently available "
            "for general-purpose reasoning. Local tools and web fallback "
            "are still available.",
            "provider-unavailable",
        )

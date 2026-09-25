class RAKIBRouter:
    def __init__(self):
        self.providers = []

    def register(self, name, handler, priority=100):
        if callable(handler):
            self.providers.append((priority, name, handler))
            self.providers.sort(key=lambda x: x[0])

    def ask(self, command):
        errors = []

        for _, name, handler in self.providers:
            try:
                result = handler(command)

                if result and str(result).strip():
                    return str(result).strip(), name

            except Exception as e:
                errors.append(f"{name}: {e}")

        return (
            "I'm online, but no external AI provider is currently available.",
            "rakib-core"
        )

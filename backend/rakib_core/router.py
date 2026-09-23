class RAKIBRouter:
    def __init__(self):
        self.providers = {}

    def register(self, name, handler):
        if callable(handler):
            self.providers[name] = handler

    def ask(self, command):
        for name, handler in self.providers.items():
            try:
                result = handler(command)
                if result:
                    return str(result).strip(), name
            except Exception as e:
                print(f"[{name}] {e}")

        return (
            "I'm online, but no AI provider is currently available.",
            "rakib-core"
        )

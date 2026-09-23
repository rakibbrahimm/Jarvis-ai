class RAKIBRouter:
    def __init__(self):
        self.providers = {}

    def register(self, name, handler):
        if callable(handler):
            self.providers[name] = handler

    def ask(self, command, preferred=None):
        command = (command or "").strip()
        if not command:
            return "I didn't receive a command.", "rakib-core"

        order = []
        if preferred in self.providers:
            order.append(preferred)

        for name in self.providers:
            if name not in order:
                order.append(name)

        for name in order:
            try:
                result = self.providers[name](command)
                if result:
                    return str(result).strip(), name
            except Exception as e:
                print(f"Provider {name} error:", e)

        return "RAKIB could not get a response.", "rakib-core"

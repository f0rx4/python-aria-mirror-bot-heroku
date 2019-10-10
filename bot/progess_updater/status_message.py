class StatusMessage:
    def __int__(self, update, context):
        self.update = update
        self.context = context
        self.message = update.message
        self.uid = self.update.effective_chat.id

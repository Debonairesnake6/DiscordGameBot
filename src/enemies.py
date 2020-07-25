class Enemies:

    def __init__(self):
        self.hi = "hi"

    async def printMe(self, message):
        await message.message.channel.send('hello')
class Enemies:

    def __init__(self, message):
        self.hi = "hi"
        self.message = message

        self.printMe()

    async def printMe(self):
        print(self.hi)
        await self.message.channel.send('hello')
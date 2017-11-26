from discord.ext import commands

class Test:
    @commands.group(invoke_without_command=True)
    async def test(self, ctx, *args):
        print('hello')
        print(ord(args[0]))

    @test.command(name='test')
    async def test_test(self, ctx):
        print('subcommand')

    @test.before_invoke
    async def before(self, ctx):
        print('before')


def setup(bot):
    bot.add_cog(Test())
"""A browser closing the live view is not an error in the log (R32)."""

import asyncio

from jarvis import web


class Loop:
    def __init__(self):
        self.passed_on = []

    def default_exception_handler(self, context):
        self.passed_on.append(context)


def test_a_reset_connection_is_dropped_and_anything_else_passed_on():
    loop = Loop()
    web.quiet_disconnects(loop, {"message": "Exception in callback", "exception": ConnectionResetError(10054)})
    web.quiet_disconnects(loop, {"message": "Exception in callback", "exception": ValueError("real")})
    web.quiet_disconnects(loop, {"message": "Task was destroyed but it is pending!"})
    assert [type(c.get("exception")) for c in loop.passed_on] == [ValueError, type(None)]


def test_the_server_loop_gets_the_handler_at_startup():
    async def installed():
        async with web._lifespan(web.app):
            return asyncio.get_running_loop().get_exception_handler()
    assert asyncio.run(installed()) is web.quiet_disconnects

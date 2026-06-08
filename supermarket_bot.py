Starting Container
2026-06-08 11:33:01,347 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE/getMe "HTTP/1.1 200 OK"
2026-06-08 11:33:01,541 - __main__ - INFO - Database tayyor!
2026-06-08 11:33:01,692 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE/deleteWebhook "HTTP/1.1 200 OK"
2026-06-08 11:33:01,693 - telegram.ext.Application - INFO - Application started
              ^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-06-08 11:33:06,288 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE/getUpdates "HTTP/1.1 409 Conflict"
  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 525, in decorator
2026-06-08 11:33:06,289 - telegram.ext.Updater - ERROR - Error while getting Updates: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
    result = await func(self, *args, **kwargs)  # skipcq: PYL-E1102
2026-06-08 11:33:06,289 - telegram.ext.Application - ERROR - No error handlers are registered, logging exception.
Traceback (most recent call last):
  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_updater.py", line 688, in _network_loop_retry
    if not await action_cb():
           ^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_updater.py", line 384, in polling_action_cb
    raise exc
  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_updater.py", line 373, in polling_action_cb
    updates = await self.bot.get_updates(
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_extbot.py", line 558, in get_updates
    updates = await super().get_updates(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 3584, in get_updates
    await self._post(
  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 613, in _post
    return await self._do_post(
           ^^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_extbot.py", line 340, in _do_post
    return await super()._do_post(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/telegram/_bot.py", line 641, in _do_post
    return await request.post(
           ^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/telegram/request/_baserequest.py", line 200, in post
    result = await self._request_wrapper(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/venv/lib/python3.12/site-packages/telegram/request/_baserequest.py", line 381, in _request_wrapper
    raise Conflict(message)
telegram.error.Conflict: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
2026-06-08 11:33:13,330 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE/getUpdates "HTTP/1.1 200 OK"
2026-06-08 11:33:13,331 - telegram.ext.Application - ERROR - No error handlers are registered, logging exception.
Traceback (most recent call last):
  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_application.py", line 1234, in process_update
    await coroutine
  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_basehandler.py", line 157, in handle_update
    return await self.callback(update, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/supermarket_bot.py", line 191, in start
    reply_markup=main_reply_keyboard()
                 ^^^^^^^^^^^^^^^^^^^^^
  File "/app/supermarket_bot.py", line 65, in main_reply_keyboard
    return ReplyKeyboardMarkup(
           ^^^^^^^^^^^^^^^^^^^^
TypeError: ReplyKeyboardMarkup.__init__() got an unexpected keyword argument 'persistent'
2026-06-08 11:33:23,479 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE/getUpdates "HTTP/1.1 200 OK"
2026-06-08 11:33:25,675 - httpx - INFO - HTTP Request: POST https://api.telegram.org/bot8617768849:AAGeu2DFAZrJYi1kJqanD2M-yEnbERqruAE/getUpdates "HTTP/1.1 200 OK"
2026-06-08 11:33:25,676 - telegram.ext.Application - ERROR - No error handlers are registered, logging exception.
Traceback (most recent call last):
  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_application.py", line 1234, in process_update
    await coroutine
  File "/opt/venv/lib/python3.12/site-packages/telegram/ext/_basehandler.py", line 157, in handle_update
    return await self.callback(update, context)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/supermarket_bot.py", line 191, in start
    reply_markup=main_reply_keyboard()
                 ^^^^^^^^^^^^^^^^^^^^^
  File "/app/supermarket_bot.py", line 65, in main_reply_keyboard
    return ReplyKeyboardMarkup(
           ^^^^^^^^^^^^^^^^^^^^
TypeError: ReplyKeyboardMarkup.__init__() got an unexpected keyword argument 'persistent'

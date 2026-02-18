from pyrogram import Client, types
from httpx import AsyncClient, TimeoutException
from pytz import timezone as _timezone
from io import BytesIO
from itertools import cycle, groupby
from bisect import bisect_left
from functools import partial

import math
import asyncio
import typing

from parse_data import get_all_star_gifts, check_is_star_gift_upgradable
from star_gifts_data import StarGiftData, StarGiftsData

import utils
import constants
import config


timezone = _timezone(config.TIMEZONE)

NULL_STR = ""

T = typing.TypeVar("T")
STAR_GIFT_RAW_T = dict[str, typing.Any]
UPDATE_GIFTS_QUEUE_T = asyncio.Queue[tuple[StarGiftData, StarGiftData]]

BASIC_REQUEST_DATA = {
    "parse_mode": "HTML",
    "disable_web_page_preview": True
}

BOTS_AMOUNT = len(config.BOT_TOKENS)

logger = utils.get_logger(
    name=config.SESSION_NAME,
    log_filepath=constants.LOG_FILEPATH,
    console_log_level=config.CONSOLE_LOG_LEVEL,
    file_log_level=config.FILE_LOG_LEVEL
)

# --- state file (data/star_gifts.json) ---
STAR_GIFTS_DATA = StarGiftsData.load(config.DATA_FILEPATH)
last_star_gifts_data_saved_time: int | None = None

# --- Bot API client (for sending notifications) ---
BOT_HTTP_CLIENT: AsyncClient | None = None
BOT_TOKENS_CYCLE = cycle(config.BOT_TOKENS)


def _require_bot_tokens():
    if BOTS_AMOUNT <= 0:
        raise SystemExit(
            "BOT_TOKENS is empty. Add at least one bot token in .env / config.py to send alerts."
        )


@typing.overload
async def bot_send_request(
    method: str,
    data: dict[str, typing.Any] | None
) -> dict[str, typing.Any]: ...


@typing.overload
async def bot_send_request(
    method: typing.Literal["editMessageText"],
    data: dict[str, typing.Any]
) -> dict[str, typing.Any] | None: ...


async def bot_send_request(
    method: str,
    data: dict[str, typing.Any] | None = None
) -> dict[str, typing.Any] | None:
    if BOT_HTTP_CLIENT is None:
        raise RuntimeError("BOT_HTTP_CLIENT is not initialized")

    logger.debug(f"Sending request {method} with data: {data}")

    retries = BOTS_AMOUNT
    response = None

    for bot_token in BOT_TOKENS_CYCLE:
        retries -= 1
        if retries < 0:
            break

        try:
            response = (await BOT_HTTP_CLIENT.post(
                f"/bot{bot_token}/{method}",
                json=data
            )).json()

        except TimeoutException:
            logger.warning(f"Timeout while sending {method} with data: {data}")
            continue

        if response.get("ok"):
            return response.get("result")

        # Telegram returns ok=false for edit when content is identical
        if (
            method == "editMessageText"
            and isinstance(response.get("description"), str)
            and "message is not modified" in response["description"]
        ):
            return None

    raise RuntimeError(f"Failed to send request to Telegram API: {response}")


async def star_gifts_data_saver(star_gifts: list[StarGiftData]) -> None:
    """
    Saves star gifts data to data/star_gifts.json with throttling (DATA_SAVER_DELAY).
    """
    global last_star_gifts_data_saved_time

    now = utils.get_current_timestamp()
    if last_star_gifts_data_saved_time and now - last_star_gifts_data_saved_time < config.DATA_SAVER_DELAY:
        return

    STAR_GIFTS_DATA.star_gifts = star_gifts
    STAR_GIFTS_DATA.save(config.DATA_FILEPATH)

    last_star_gifts_data_saved_time = now


async def detector(
    app: Client,
    new_gift_callback: typing.Callable[[StarGiftData], typing.Coroutine[None, None, typing.Any]] | None = None,
    update_gifts_queue: UPDATE_GIFTS_QUEUE_T | None = None
) -> None:
    if new_gift_callback is None and update_gifts_queue is None:
        raise ValueError("At least one of new_gift_callback or update_gifts_queue must be provided")

    while True:
        logger.debug("Checking for new gifts / updates...")

        if not app.is_connected:
            await app.start()

        _, all_star_gifts_dict = await get_all_star_gifts(app)

        # first run init
        if not STAR_GIFTS_DATA.star_gifts:
            await star_gifts_data_saver(list(all_star_gifts_dict.values()))
            logger.info("Initial star gifts saved to file.")

        old_star_gifts_dict = {g.id: g for g in STAR_GIFTS_DATA.star_gifts}

        # new gifts
        new_star_gifts = {
            gid: g for gid, g in all_star_gifts_dict.items()
            if gid not in old_star_gifts_dict
        }

        if new_star_gifts and new_gift_callback:
            logger.info(f"Found {len(new_star_gifts)} new gifts: [{', '.join(map(str, new_star_gifts.keys()))}]")
            for _, star_gift in new_star_gifts.items():
                await new_gift_callback(star_gift)

        # updates for limited gifts (available_amount decreased)
        if update_gifts_queue:
            for gid, old_gift in old_star_gifts_dict.items():
                new_gift = all_star_gifts_dict.get(gid)

                if new_gift is None:
                    logger.warning("Star gift missing in new gifts, skipping update", extra={"star_gift_id": str(gid)})
                    continue

                # preserve message_id so we can edit the message later
                new_gift.message_id = old_gift.message_id

                if new_gift.available_amount < old_gift.available_amount:
                    update_gifts_queue.put_nowait((old_gift, new_gift))

        # persist updated data if new gifts appeared
        if new_star_gifts:
            await star_gifts_data_saver(list(all_star_gifts_dict.values()))

        await asyncio.sleep(config.CHECK_INTERVAL)


def get_notify_text(star_gift: StarGiftData) -> str:
    is_limited = star_gift.is_limited

    available_percentage, available_percentage_is_same = (
        utils.pretty_float(
            math.ceil(star_gift.available_amount / star_gift.total_amount * 100 * 100) / 100,
            get_is_same=True
        )
        if is_limited else (NULL_STR, False)
    )

    return config.NOTIFY_TEXT.format(
        title=config.NOTIFY_TEXT_TITLES[is_limited],
        number=star_gift.number,
        id=star_gift.id,
        total_amount=(
            config.NOTIFY_TEXT_TOTAL_AMOUNT.format(
                total_amount=utils.pretty_int(star_gift.total_amount)
            )
            if is_limited else NULL_STR
        ),
        available_amount=(
            config.NOTIFY_TEXT_AVAILABLE_AMOUNT.format(
                available_amount=utils.pretty_int(star_gift.available_amount),
                same_str=(NULL_STR if available_percentage_is_same else "~"),
                available_percentage=available_percentage,
                updated_datetime=utils.get_current_datetime(timezone)
            )
            if is_limited else NULL_STR
        ),
        sold_out=(
            config.NOTIFY_TEXT_SOLD_OUT.format(
                sold_out=utils.format_seconds_to_human_readable(
                    star_gift.last_sale_timestamp - star_gift.first_appearance_timestamp
                )
            )
            if star_gift.last_sale_timestamp and star_gift.first_appearance_timestamp else NULL_STR
        ),
        price=utils.pretty_int(star_gift.price),
        convert_price=utils.pretty_int(star_gift.convert_price)
    )


async def process_new_gift(app: Client, star_gift: StarGiftData) -> None:
    """
    Sends sticker + message to NOTIFY_CHAT_ID.
    Stores message_id in state for later edits.
    """
    _require_bot_tokens()

    sticker_message = await app.send_sticker(
        chat_id=config.NOTIFY_CHAT_ID,
        sticker=star_gift.sticker_file_id
    )

    await asyncio.sleep(config.NOTIFY_AFTER_STICKER_DELAY)

    message = await bot_send_request(
        "sendMessage",
        {
            "chat_id": config.NOTIFY_CHAT_ID,
            "text": get_notify_text(star_gift),
            "reply_to_message_id": sticker_message.id
        } | BASIC_REQUEST_DATA
    )

    await asyncio.sleep(config.NOTIFY_AFTER_TEXT_DELAY)

    star_gift.message_id = message["message_id"] if isinstance(message, dict) else None

    # persist with new message_id
    all_gifts = STAR_GIFTS_DATA.star_gifts + [star_gift]
    await star_gifts_data_saver(all_gifts)

    logger.info("New gift notified", extra={"star_gift_id": str(star_gift.id)})


async def process_update_gifts(update_gifts_queue: UPDATE_GIFTS_QUEUE_T) -> None:
    """
    Processes limited gifts availability updates and edits existing messages.
    """
    _require_bot_tokens()

    while True:
        old_star_gift, new_star_gift = await update_gifts_queue.get()

        try:
            # sold out detection
            if new_star_gift.available_amount <= 0 and old_star_gift.available_amount > 0:
                new_star_gift.last_sale_timestamp = utils.get_current_timestamp()

            # update stored state
            for i, g in enumerate(STAR_GIFTS_DATA.star_gifts):
                if g.id == new_star_gift.id:
                    STAR_GIFTS_DATA.star_gifts[i] = new_star_gift
                    break

            await star_gifts_data_saver(STAR_GIFTS_DATA.star_gifts)

            # edit telegram message
            if new_star_gift.message_id:
                await bot_send_request(
                    "editMessageText",
                    {
                        "chat_id": config.NOTIFY_CHAT_ID,
                        "message_id": new_star_gift.message_id,
                        "text": get_notify_text(new_star_gift)
                    } | BASIC_REQUEST_DATA
                )

            logger.info(
                "Gift updated",
                extra={
                    "star_gift_id": str(new_star_gift.id),
                    "available_amount": str(new_star_gift.available_amount),
                }
            )

        except Exception as e:
            logger.exception(f"Failed to process update gift: {e}")

        finally:
            update_gifts_queue.task_done()


async def star_gifts_upgrades_checker(app: Client) -> None:
    """
    Checks upgrade availability for gifts and notifies NOTIFY_UPGRADES_CHAT_ID.
    """
    if not config.NOTIFY_UPGRADES_CHAT_ID:
        return

    _require_bot_tokens()

    while True:
        try:
            if not app.is_connected:
                await app.start()

            # gifts sorted by id for stable processing
            gifts_sorted = sorted(STAR_GIFTS_DATA.star_gifts, key=lambda g: g.id)

            # check in small chunks per cycle
            batch_size = max(1, config.CHECK_UPGRADES_PER_CYCLE)
            for i in range(0, len(gifts_sorted), batch_size):
                batch = gifts_sorted[i:i + batch_size]

                for star_gift in batch:
                    if star_gift.is_upgradable:
                        continue

                    can_upgrade = await check_is_star_gift_upgradable(app, star_gift.id)
                    if not can_upgrade:
                        continue

                    # notify
                    sticker_message = await app.send_sticker(
                        chat_id=config.NOTIFY_UPGRADES_CHAT_ID,
                        sticker=star_gift.sticker_file_id
                    )

                    await asyncio.sleep(config.NOTIFY_AFTER_STICKER_DELAY)

                    await bot_send_request(
                        "sendMessage",
                        {
                            "chat_id": config.NOTIFY_UPGRADES_CHAT_ID,
                            "text": config.NOTIFY_UPGRADES_TEXT.format(id=star_gift.id),
                            "reply_to_message_id": sticker_message.id
                        } | BASIC_REQUEST_DATA
                    )

                    star_gift.is_upgradable = True
                    await star_gifts_data_saver(STAR_GIFTS_DATA.star_gifts)

                await asyncio.sleep(config.CHECK_INTERVAL)

        except Exception as e:
            logger.exception(f"Upgrades checker error: {e}")
            await asyncio.sleep(5)


async def main() -> None:
    """
    Entrypoint.
    """
    global BOT_HTTP_CLIENT

    logger.info("Starting Telegram Star Gifts Monitor...")

    # init bot http client if tokens exist
    _require_bot_tokens()
    BOT_HTTP_CLIENT = AsyncClient(
        base_url="https://api.telegram.org/",
        timeout=config.HTTP_REQUEST_TIMEOUT
    )
    # --- startup notification ---
    try:
        await bot_send_request(
            "sendMessage",
            {
                "chat_id": config.NOTIFY_CHAT_ID,
                "text": "✅ Star Gifts Monitor started"
            } | BASIC_REQUEST_DATA
        )
    except Exception as e:
        logger.warning(f"Failed to send startup message: {e}")


    app = Client(
        name=config.SESSION_NAME,
        api_id=config.API_ID,
        api_hash=config.API_HASH
    )

    update_gifts_queue: UPDATE_GIFTS_QUEUE_T | None = (
        UPDATE_GIFTS_QUEUE_T()
        if BOTS_AMOUNT > 0 else None
    )

    # background: update processor
    if update_gifts_queue:
        asyncio.create_task(process_update_gifts(update_gifts_queue))

    # background: upgrades checker
    if config.NOTIFY_UPGRADES_CHAT_ID:
        asyncio.create_task(star_gifts_upgrades_checker(app))

    await detector(
        app=app,
        new_gift_callback=partial(process_new_gift, app),
        update_gifts_queue=update_gifts_queue
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        try:
            STAR_GIFTS_DATA.save(config.DATA_FILEPATH)
        except Exception:
            pass

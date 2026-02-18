from pydantic import BaseModel, Field
from pathlib import Path

import simplejson as json

import constants


class BaseConfigModel(BaseModel, extra="ignore"):
    pass


class StarGiftData(BaseConfigModel):
    id: int
    number: int
    sticker_file_id: str
    sticker_file_name: str
    price: int
    convert_price: int
    available_amount: int
    total_amount: int
    is_limited: bool
    first_appearance_timestamp: int | None = Field(default=None)
    message_id: int | None = Field(default=None)
    last_sale_timestamp: int | None = Field(default=None)
    is_upgradable: bool = Field(default=False)


class StarGiftsData(BaseConfigModel):
    DATA_FILEPATH: Path = Field(default=None, exclude=True)
    star_gifts: list[StarGiftData] = Field(default_factory=list[StarGiftData])

    @classmethod
    def load(cls, data_filepath: Path) -> "StarGiftsData":
        try:
            with data_filepath.open("r", encoding=constants.ENCODING) as file:
                obj = cls.model_validate({
                    **json.load(file),
                    "DATA_FILEPATH": data_filepath
                })
                return obj

        except FileNotFoundError:
            return cls(DATA_FILEPATH=data_filepath)

    def save(self, path: Path | None = None) -> None:
        filepath = path or self.DATA_FILEPATH
        if not filepath:
            raise ValueError("No path specified for saving star gifts data.")

        with filepath.open("w", encoding=constants.ENCODING) as file:
            json.dump(
                obj=self.model_dump(),
                fp=file,
                indent=4,
                ensure_ascii=True,
                sort_keys=False
            )

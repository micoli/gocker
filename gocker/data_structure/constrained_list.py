from dataclasses import dataclass


@dataclass
class _ConstrainedListItem:
    index: int
    item: object


class ConstrainedList:
    def __init__(self, max_length: int):
        self.__stack: list[_ConstrainedListItem] = []
        self.__index = 0
        self.__max_length = max_length

    def append(self, data: object):
        if len(self.__stack) == self.__max_length:
            self.__stack.pop(0)
        self.__index += 1
        self.__stack.append(_ConstrainedListItem(
            self.__index,
            data
        ))

    def get_from(self, index=0):
        return [(item.index, item.item) for item in self.__stack if item.index > index]

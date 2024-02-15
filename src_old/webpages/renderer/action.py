from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Any, Union
import random
from selenium import webdriver
from .utils import find_clickable_elts, filter_clickable_elts


class ActionType(Enum):
    """An enumeration to describe the type of action"""

    CLICK = "click"
    SCROLL = "scroll"
    HOVER = "hover"


class Action(ABC):
    """A class to describe an action that a user can perform on a website"""

    def __init__(self, action_type: ActionType, argument: Optional[Any] = None):
        self.action_type = action_type
        self.argument = argument

    @abstractmethod
    def perform(self, driver: webdriver.Chrome):
        pass

    @staticmethod
    def get_random_action(driver: webdriver.Chrome, *args, **kwargs) -> "Action":
        """Randomly choose an action type and return its get_random_action result"""
        action_classes: List["Action"] = [ClickAction, ScrollAction]
        chosen_action_class = random.choice(action_classes)
        return chosen_action_class.get_random_action(driver, *args, **kwargs)

    def __repr__(self) -> str:
        return f"Action({self.action_type}, {self.argument})"

    def __eq__(self, action: "Action") -> bool:
        return (self.action_type == action.action_type) and (
            self.argument == action.argument
        )

    def __hash__(self):
        return hash((self.action_type, self.argument))


class ClickAction(Action):
    """A class to describe a click action"""

    def __init__(self, argument: str):
        super().__init__(action_type=ActionType.CLICK, argument=argument)

    def perform(self, driver: webdriver.Chrome):
        # Go to link provided as argument
        driver.get(self.argument)

    @staticmethod
    def get_random_action(
        driver: webdriver.Chrome, port: int, *args, **kwargs
    ) -> "ClickAction":
        """Get a random click action"""
        clickables: List[str] = filter_clickable_elts(
            find_clickable_elts(driver), url=f"http://localhost:{port}"
        )
        if len(clickables) == 0:
            return ClickAction(argument=f"http://localhost:{port}")
        link: str = random.choice(clickables)
        return ClickAction(argument=link)


class ScrollAction(Action):
    """A class to describe a scroll action"""

    BOTTOM: str = "bottom"
    TOP: str = "top"

    def __init__(self, argument: Union[int, str]):
        super().__init__(action_type=ActionType.SCROLL, argument=argument)

    def perform(self, driver: webdriver.Chrome):
        if isinstance(self.argument, int):
            driver.execute_script(f"window.scrollBy(0, {self.argument})")
        elif self.argument == self.BOTTOM:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        elif self.argument == self.TOP:
            driver.execute_script("window.scrollTo(0, 0)")

    @staticmethod
    def get_random_action(driver: webdriver.Chrome, *args, **kwargs) -> "ScrollAction":
        """Get a random scroll action"""
        options: List[str] = [ScrollAction.BOTTOM, ScrollAction.TOP, "random"]
        option: str = random.choice(options)
        if option == "random":
            max_scroll_height: int = driver.execute_script(
                "return document.body.scrollHeight"
            )
            return ScrollAction(argument=random.randint(0, max_scroll_height))
        return ScrollAction(argument=option)

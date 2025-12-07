"""Provides classes for scraping blackout periods from the electric energy operator website."""

import re, logging
import aiohttp

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from parsel import Selector
from calmjs.parse import es5
from calmjs.parse.unparsers.extractor import ast_to_dict

from .const import PowerOffGroup
from .entities import BlackoutPeriod

START_URL = "https://www.dtek-krem.com.ua/ua/"
URL = "https://www.dtek-krem.com.ua/ua/shutdowns"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko/20100101 Firefox/145.0"

LOGGER = logging.getLogger(__name__)

class DataScraper:
    """Class for scraping blackout periods from the $URL website."""

    def __init__(self, group: PowerOffGroup) -> None:
        """Initialize the DataScrapper object."""
        self.playwright = async_playwright()
        self.group = group

    async def validate(self) -> bool:
        # TODO: add error handling
        browser = await self.playwright.chromium.launch()
        page = await browser.new_page()
        response = await page.goto(START_URL, wait_until="networkidle")
        await browser.close()
        return response.status == 200

    @staticmethod
    def merge_periods(periods: list[BlackoutPeriod]) -> list[BlackoutPeriod]:
        if not periods:
            return []

        periods.sort(key=lambda x: x.start)

        merged_periods = [periods[0]]
        for current in periods[1:]:
            last = merged_periods[-1]
            if current.start <= last.end:  # Overlapping or contiguous periods
                last.end = max(last.end, current.end)
                continue
            merged_periods.append(current)

        return merged_periods

    async def get_blackout_periods(self) -> list[BlackoutPeriod]:
        # TODO: add error handling
        browser = await self.playwright.chromium.launch()
        page = await browser.new_page()
        response = await page.goto(START_URL, wait_until="networkidle")
        await browser.close()

        content = response.text()
        LOGGER.debug("Script: %s", content)
        html = Selector(content)
        # soup = BeautifulSoup(content, "html.parser")
        # results = []

        # s = soup.find("script:contains('DisconSchedule.fact')")
        s = html.xpath(".//script[contains(., 'DisconSchedule.fact')]")
        LOGGER.debug("Script: %s", s)

        js_text = s.xpath(".//text()").get()
        LOGGER.debug("js_text: %s", js_text)
        schedules = ast_to_dict(es5(js_text))
        LOGGER.debug("schedules: %s", schedules)
        fact = schedules['DisconSchedule.fact']
        LOGGER.debug("fact: %s", fact)

        today_key = str(fact['today'])
        LOGGER.debug("today_key: %s", today_key)
        today = fact['data'][today_key] # for all groups
        current = today['GPV6.1'] # my group
        LOGGER.debug("current: %s", current)


            
            # scale_hours = soup.find_all("div", class_="scale_hours")
            # if len(scale_hours) > 0:
            #     scale_hours_el = scale_hours[0].find_all("div", class_="scale_hours_el")
            #     for item in scale_hours_el:
            #         if item.find("span", class_="hour_active"):
            #             start, end = self._parse_item(item)
            #             results.append(BlackoutPeriod(start, end, today=True))
            #     results = self.merge_periods(results)
            # if len(scale_hours) > 1:
            #     tomorrow_results = []
            #     scale_hours_el_tomorrow = scale_hours[1].find_all("div", class_="scale_hours_el")
            #     for item in scale_hours_el_tomorrow:
            #         if item.find("span", class_="hour_active"):
            #             start, end = self._parse_item(item)
            #             tomorrow_results.append(BlackoutPeriod(start, end, today=False))
            #     results += self.merge_periods(tomorrow_results)

        return current

    def _parse_item(self, item: BeautifulSoup) -> tuple[int, int]:
        start_hour = item.find("i", class_="hour_info_from")
        end_hour = item.find("i", class_="hour_info_to")
        if start_hour and end_hour:
            return int(start_hour.text.split(':')[0]), int(end_hour.text.split(':')[0])
        raise ValueError(f"Time period not found in the input string: {item.text}")

"""Parse https://www.residentadvisor.net/events/us/washingtondc"""

import re
import requests
import bs4
from bs4 import BeautifulSoup
from word2number import w2n

class SoupEvent(bs4.element.Tag):
    """Extend event element.
Properties:
    name,
    venue,
    date,
    number_of_attendees
"""

    def __init__(self):
        super().__init__()

    @classmethod
    def convert_class(cls, obj):
        """Convert obj to this class."""
        try:
            obj.__class__ = cls
        except:
            raise TypeError(f"Could not convert {obj.__class__.__name__}:\n {obj}")

    @property
    def name(self):
        """Retrieves event name."""
        return self.find(class_='event-title').a.text

    @property
    def venue(self):
        """Retrieves event venue.
    """
        regex = re.compile("star-rating (.*)")
        return self.find(href=re.compile("club")).text

    @property
    def date(self):
        """Returns event date as string."""
        return self.find("time", {"itemprop" : "startDate"})['datetime']

    @property
    def number_of_attendees(self):
        """returns number of attendees"""
        attending = self.find(class_ ='attending')
        if attending:
            return int(attending.span.text)
        return None

    def as_dict(self):
        """Return dict of event elements"""
        return {
            'name' : self.name,
            'venue' : self.venue,
            'date' : self.date,
            'number_of_attendees' : self.number_of_attendees
        }

class ScrapePage:
    """Page class that can return contents as soup, next page."""

    def __init__(self, url):
        self.url = url
        print(f"Scraping {url}...")
        self.soup = BeautifulSoup(requests.get(self.url).content, 'html.parser')
        self.events = self._get_events()
        print(f"Found {len(self.events)} events.")

    @property
    def next(self):
        """url of the next page, if any.
           Found in #liNext a[href]"""

        next_page = self.soup.find(id='liNext').a
        if next_page.has_attr('href'):
            return requests.compat.urljoin(self.url, next_page['href'])

    def _get_events(self):
        """Return a list of SoupEvents.
        Found in .event-item"""
        events = self.soup.select(".event-item")
        for event in events:
            SoupEvent.convert_class(event)
        return events

    def event_dicts(self):
        """Returns list of dicts of events."""
        return [event.as_dict() for event in self.events]

class EventScraper:
    """Scrapes residentadvisor, returns event listings.
Parameters:
    base_url : Starting URL to start scraping from

Usage:
import pandas as pd
from parseevents import EventScraper
url = 'https://www.residentadvisor.net/events/us/washingtondc'
es = EventScraper(url)
es.scrape(limit = 50)
df = pd.DataFrame(es.event_dicts)
"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.current_url = base_url
        self.page = ScrapePage(base_url)
        self.next_url = self.page.next
        self.events = self.page.events
        self._page_count = 1

    @property
    def offset(self):
        """Current number of events retrieved."""
        return len(self.events)

    @property
    def event_dicts(self):
        """List of dicts of events."""
        return [event.as_dict() for event in self.events]

    @property
    def page_count(self):
        """Count of pages scraped."""
        return self._page_count

    def scrape(self, url = None, limit: int = None):
        """Traverses pages to find events.
Optional parameters:
    url : to re-start scraping from a point other than the initialized url.
    limit : If limit is set, stops when length of events is
            greater than or equal to limit."""
        # TODO: implement starting offset
        if url:
            self.next_url = url
        while self.next_url:
            if limit and (self.offset > limit):
                break
            self.page = ScrapePage(self.next_url)
            self.events.extend(self.page.events)
            self._page_count += 1
            self.current_url = self.next_url
            self.next_url = self.page.next

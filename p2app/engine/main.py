# p2app/engine/main.py
#
# ICS 33 Fall 2023
# Project 2: Learning to Fly
#
# An object that represents the engine of the application.
#
# This is the outermost layer of the part of the program that you'll need to build,
# which means that YOU WILL DEFINITELY NEED TO MAKE CHANGES TO THIS FILE.

from p2app.events import *
import sqlite3


class Engine:
    """An object that represents the application's engine, whose main role is to
    process events sent to it by the user interface, then generate events that are
    sent back to the user interface in response, allowing the user interface to be
    unaware of any details of how the engine is implemented.
    """

    def __init__(self):
        """Initializes the engine"""
        self.connection = None

    def process_event(self, event):
        """A generator function that processes one event sent from the user interface,
        yielding zero or more events in response."""
        # This is a way to write a generator function that always yields zero values.
        # You'll want to remove this and replace it with your own code, once you start
        # writing your engine, but this at least allows the program to run.
        # yield from ()

        # Application-level events
        if isinstance(event, OpenDatabaseEvent):
            try:
                database_path = event.path()
                self.connection = sqlite3.connect(database_path, isolation_level=None)
                self.connection.execute('PRAGMA foreign_keys = ON;')  # foreign key constraints
                yield DatabaseOpenedEvent(database_path)
            except Exception as e:
                # If opening the database fails, generate a DatabaseOpenFailedEvent
                yield DatabaseOpenFailedEvent(str(e))

        elif isinstance(event, QuitInitiatedEvent):
            yield EndApplicationEvent()

        elif isinstance(event, CloseDatabaseEvent):
            if self.connection is not None:
                self.connection.close()
                self.connection = None
                yield DatabaseClosedEvent()

        # Continent-related events
        elif isinstance(event, StartContinentSearchEvent):
            results = self.search_continents('', event.continent_code(), event.name())
            for continent in results:
                continent_obj = Continent(continent_id=continent[0], continent_code=continent[1], name=continent[2])
                yield ContinentSearchResultEvent(continent_obj)

        elif isinstance(event, LoadContinentEvent):
            results = self.search_continents(event.continent_id(), '', '')
            for continent in results:
                continent_obj = Continent(continent_id=continent[0], continent_code=continent[1], name=continent[2])
                yield ContinentLoadedEvent(continent_obj)

        elif isinstance(event, SaveContinentEvent):
            try:
                continent = event.continent()
                if continent is not None:
                    # Construct the SQL UPDATE query to update the continent
                    query = "UPDATE continent SET continent_code = ?, name = ? WHERE continent_id = ?"

                    # Execute the query with the provided data
                    cursor = self.connection.cursor()
                    cursor.execute(query, (continent.continent_code, continent.name, continent.continent_id))
                    self.connection.commit()

                    yield ContinentSavedEvent(continent)
            except Exception as e:
                yield SaveContinentFailedEvent(str(e))

        elif isinstance(event, SaveNewContinentEvent):
            try:
                continent = event.continent()
                if continent is not None:
                    continent_code = continent.continent_code
                    name = continent.name
                    # Construct the SQL INSERT query
                    query = f"INSERT INTO continent (continent_code, name) VALUES (?, ?)"

                    # Execute the query with the provided data
                    cursor = self.connection.cursor()
                    cursor.execute(query, (continent_code, name))
                    self.connection.commit()

                    # Retrieve the last inserted row ID
                    last_row_id = cursor.lastrowid

                    # Create a new Continent object with the generated continent_id
                    new_continent = Continent(continent_id=last_row_id, continent_code=continent_code,
                                              name=name)

                    yield ContinentSavedEvent(new_continent)

            except Exception as e:
                yield SaveContinentFailedEvent(str(e))

        # Country-related events
        elif isinstance(event, StartCountrySearchEvent):
            results = self.search_countries('', event.country_code(), event.name())
            for country in results:
                country_obj = Country(
                    country_id=country[0],
                    country_code=country[1],
                    name=country[2],
                    continent_id=country[3],
                    wikipedia_link=country[4],
                    keywords=country[5]
                )
                yield CountrySearchResultEvent(country_obj)

        elif isinstance(event, LoadCountryEvent):
            results = self.search_countries(event.country_id(), '', '')
            for country in results:
                country_obj = Country(
                    country_id=country[0],
                    country_code=country[1],
                    name=country[2],
                    continent_id=country[3],
                    wikipedia_link=country[4],
                    keywords=country[5]
                )
                yield CountryLoadedEvent(country_obj)

        elif isinstance(event, SaveNewCountryEvent):
            try:
                country = event.country()
                if country is not None:
                    # Construct the SQL INSERT query to add a new country
                    query = "INSERT INTO country (country_code, name, continent_id, wikipedia_link, keywords) VALUES (?, ?, ?, ?, ?)"

                    # Execute the query with the provided data
                    cursor = self.connection.cursor()
                    cursor.execute(query, (country.country_code, country.name, country.continent_id, country.wikipedia_link, country.keywords))
                    self.connection.commit()

                    # Retrieve the last inserted row ID
                    last_row_id = cursor.lastrowid

                    # Create a new Country object with the generated country_id
                    new_country = Country(
                        country_id=last_row_id,
                        country_code=country.country_code,
                        name=country.name,
                        continent_id=country.continent_id,
                        wikipedia_link=country.wikipedia_link,
                        keywords=country.keywords
                    )

                    yield CountrySavedEvent(new_country)

            except Exception as e:
                yield SaveCountryFailedEvent(str(e))

        elif isinstance(event, SaveCountryEvent):
            try:
                country = event.country()
                if country is not None:
                    # Construct the SQL UPDATE query to update the country
                    query = "UPDATE country SET country_code = ?, name = ?, continent_id = ?, wikipedia_link = ?, keywords = ? WHERE country_id = ?"

                    # Execute the query with the provided data
                    cursor = self.connection.cursor()
                    cursor.execute(query, (
                    country.country_code, country.name, country.continent_id, country.wikipedia_link, country.keywords,
                    country.country_id))
                    self.connection.commit()

                    yield CountrySavedEvent(country)

            except Exception as e:
                yield SaveCountryFailedEvent(str(e))

        # Region-related events
        elif isinstance(event, StartRegionSearchEvent):
            results = self.search_regions('', event.region_code(), event.local_code(), event.name())
            for region in results:
                region_obj = Region(
                    region_id=region[0],
                    region_code=region[1],
                    local_code=region[2],
                    name=region[3],
                    continent_id=region[4],
                    country_id=region[5],
                    wikipedia_link=region[6],
                    keywords=region[7]
                )
                yield RegionSearchResultEvent(region_obj)

        elif isinstance(event, LoadRegionEvent):
            # Handle region search
            results = self.search_regions(event.region_id(), '', '', '')
            for region in results:
                region_obj = Region(
                    region_id=region[0],
                    region_code=region[1],
                    local_code=region[2],
                    name=region[3],
                    continent_id=region[4],
                    country_id=region[5],
                    wikipedia_link=region[6],
                    keywords=region[7]
                )
                yield RegionLoadedEvent(region_obj)

        elif isinstance(event, SaveRegionEvent):
            try:
                region = event.region()
                if region is not None:
                    # Construct the SQL UPDATE query to update the region
                    query = "UPDATE region SET region_code = ?, local_code = ?, name = ?, continent_id = ?, country_id = ?, wikipedia_link = ?, keywords = ? WHERE region_id = ?"

                    # Execute the query with the provided data
                    cursor = self.connection.cursor()
                    cursor.execute(query, (
                        region.region_code, region.local_code, region.name, region.continent_id, region.country_id,
                        region.wikipedia_link, region.keywords, region.region_id))
                    self.connection.commit()

                    yield RegionSavedEvent(region)
            except Exception as e:
                yield SaveRegionFailedEvent(str(e))

        elif isinstance(event, SaveNewRegionEvent):
            try:
                region = event.region()
                if region is not None:
                    region_code = region.region_code
                    local_code = region.local_code
                    name = region.name
                    continent_id = region.continent_id
                    country_id = region.country_id
                    wikipedia_link = region.wikipedia_link
                    keywords = region.keywords

                    # Construct the SQL INSERT query
                    query = f"INSERT INTO region (region_code, local_code, name, continent_id, country_id, wikipedia_link, keywords) VALUES (?, ?, ?, ?, ?, ?, ?)"

                    # Execute the query with the provided data
                    cursor = self.connection.cursor()
                    cursor.execute(query,
                                   (region_code, local_code, name, continent_id, country_id, wikipedia_link, keywords))
                    self.connection.commit()

                    # Retrieve the last inserted row ID
                    last_row_id = cursor.lastrowid

                    # Create a new Region object with the generated region_id
                    new_region = Region(
                        region_id=last_row_id,
                        region_code=region_code,
                        local_code=local_code,
                        name=name,
                        continent_id=continent_id,
                        country_id=country_id,
                        wikipedia_link=wikipedia_link,
                        keywords=keywords
                    )
                    yield RegionSavedEvent(new_region)
            except Exception as e:
                yield SaveRegionFailedEvent(str(e))



    def search_continents(self, continent_id, continent_code, name):
        # Database query to search for continents
        cursor = self.connection.cursor()
        query = "SELECT * FROM continent WHERE 1=1"

        # Add conditions based on provided parameters
        if continent_id:
            query += f" AND continent_id = '{continent_id}'"
        if continent_code:
            query += f" AND continent_code = '{continent_code}'"
        if name:
            query += f" AND name = '{name}'"

        cursor.execute(query)
        results = cursor.fetchall()
        return results

    def search_countries(self, country_id, country_code, name):
        # Database query to search for countries
        cursor = self.connection.cursor()
        query = "SELECT * FROM country WHERE 1=1"

        # Add conditions based on provided parameters
        if country_id:
            query += f" AND country_id = '{country_id}'"
        if country_code:
            query += f" AND country_code = '{country_code}'"
        if name:
            query += f" AND name = '{name}'"

        cursor.execute(query)
        results = cursor.fetchall()
        return results

    def search_regions(self, region_id, region_code, local_code, name):
        # Database query to search for regions
        cursor = self.connection.cursor()
        query = "SELECT * FROM region WHERE 1=1"

        # Add conditions based on provided parameters
        if region_id:
            query += f" AND region_id = '{region_id}'"
        if region_code:
            query += f" AND region_code = '{region_code}'"
        if local_code:
            query += f" AND local_code = '{local_code}'"
        if name:
            query += f" AND name = '{name}'"

        cursor.execute(query)
        results = cursor.fetchall()
        return results




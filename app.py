import logging
from contextlib import contextmanager
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Callable
import random
import time as time_module

import yaml

from instapy import InstaPy, smart_run
from instapy.xpath_compile import xpath
from selenium.common import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.firefox import GeckoDriverManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(funcName)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler("instabot.log"), logging.StreamHandler()],
)

xpath["login_user"] = {"login_elem_no_such_exception_2", "//div[text()='Log In']"}


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, config_path: str = 'config.yaml'):
        logging.info(f"Initializing configuration from {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                logging.debug(f"Reading configuration file: {config_path}")
                config = yaml.safe_load(f)

            required_keys = ['auth', 'limits', 'targeting', 'engagement', 'schedule']
            missing_keys = [key for key in required_keys if key not in config]
            if missing_keys:
                logging.error(
                    f"Configuration validation failed. Missing keys: {missing_keys}"
                )
                raise ConfigError(f"Missing required config keys: {missing_keys}")

            logging.debug("Loading configuration values")
            self.USERNAME = config['auth']['credentials']['username']
            logging.info(f"Configured username: {self.USERNAME}")
            self.PASSWORD = "********"  # Mask password in logs
            logging.debug("Password loaded (masked)")

            self.MAX_DAILY_INTERACTIONS = config['limits']['interactions']['max_daily']
            logging.info(
                f"Maximum daily interactions set to: {self.MAX_DAILY_INTERACTIONS}"
            )

            self.LOCATIONS = config['targeting']['locations']
            logging.info(f"Loaded {len(self.LOCATIONS)} target locations")

            self.HASHTAGS = config['targeting']['hashtags']
            logging.info(f"Loaded {len(self.HASHTAGS)} target hashtags")

            self.TARGET_ACCOUNTS = config['targeting']['accounts']
            logging.info(f"Loaded {len(self.TARGET_ACCOUNTS)} target accounts")

            self.HOURLY_LIMITS = config['engagement']['hourly_limits']
            logging.info(f"Hourly interaction limits configured: {self.HOURLY_LIMITS}")

            self.ACTIVE_HOURS = config['schedule']['active_hours']
            logging.info(f"Active hours configured: {self.ACTIVE_HOURS}")

            self.BREAKS = config['schedule']['breaks']
            logging.info("Break schedule loaded")

            self.RELATIONSHIP_BOUNDS = config['limits']['relationship_bounds']
            logging.info(f"Relationship bounds set: {self.RELATIONSHIP_BOUNDS}")

            logging.info("Configuration loaded successfully")

        except yaml.YAMLError as e:
            logging.critical(f"Failed to parse YAML configuration: {str(e)}")
            raise ConfigError(f"YAML parsing error: {str(e)}")
        except KeyError as e:
            logging.critical(f"Invalid configuration structure. Missing key: {str(e)}")
            raise ConfigError(f"Missing config key: {str(e)}")
        except FileNotFoundError as e:
            logging.critical(f"Configuration file not found: {str(e)}")
            raise ConfigError(f"Config file not found: {str(e)}")


class InstagramBot:
    def __init__(self, config_path: str = 'config.yaml'):
        logging.info(f"Initializing InstagramBot with config path: {config_path}")
        self.config = Config(config_path)
        logging.info("Config loaded successfully")

        self.daily_interactions = 0
        logging.info("Daily interactions counter initialized to 0")

        self.weekend = datetime.now().weekday() >= 5
        logging.info(f"Weekend status set to: {self.weekend}")

        logging.info("Initializing schedule")
        self._init_schedule()
        logging.info("Schedule initialized successfully")

        self.last_action_time = datetime.now()
        logging.info(f"Last action time initialized to: {self.last_action_time}")

        self.session = None
        logging.info("Session initialized to None")

    @contextmanager
    def error_handling(self, action_name: str):
        logging.info(f"Entering error handling context for action: {action_name}")
        try:
            logging.debug(f"Attempting action: {action_name}")
            yield
            logging.info(f"Action completed successfully: {action_name}")
        except WebDriverException as e:
            logging.error(f"Selenium error in {action_name}: {str(e)}", exc_info=True)
            if self.session and self.session.browser:
                logging.info("Attempting to quit browser session")
                self.session.browser.quit()
                logging.info("Browser session quit successfully")
            self.session = None
            logging.info("Sleeping for 300 seconds after WebDriver error")
            time_module.sleep(300)
        except (TimeoutException, NoSuchElementException) as e:
            logging.error(f"Navigation error in {action_name}: {str(e)}", exc_info=True)
            logging.info("Sleeping for 60 seconds after navigation error")
            time_module.sleep(60)
        except RuntimeError as e:
            logging.error(f"Runtime error in {action_name}: {str(e)}", exc_info=True)
            logging.info("Sleeping for 30 seconds after runtime error")
            time_module.sleep(30)

    def _init_schedule(self):
        logging.info("Initializing schedule with breaks configuration")
        try:
            breaks_config = self.config.BREAKS
            logging.debug(f"Breaks config loaded: {breaks_config}")

            logging.info("Setting up bathroom breaks schedule")
            bathroom_breaks = []
            for period in ['morning', 'afternoon', 'evening']:
                hour_start = breaks_config['bathroom'][period]['hour_start']
                hour_end = breaks_config['bathroom'][period]['hour_end']
                random_hour = random.randint(hour_start, hour_end)
                random_minute = random.randint(0, 59)
                bathroom_breaks.append(time(random_hour, random_minute))
                logging.debug(
                    f"Added {period} bathroom break at {random_hour}:{random_minute}"
                )

            logging.info("Setting up lunch break schedule")
            lunch_hour = random.randint(
                breaks_config['lunch']['hour_start'], breaks_config['lunch']['hour_end']
            )
            lunch_minute = random.randint(0, 59)

            self.breaks = {
                'bathroom': bathroom_breaks,
                'lunch': time(lunch_hour, lunch_minute),
            }

            logging.info(
                f"Schedule initialized with lunch at {lunch_hour}:{lunch_minute}"
            )
            logging.debug(f"Complete break schedule: {self.breaks}")

        except KeyError as e:
            error_msg = f"Invalid breaks configuration: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise ConfigError(error_msg)

    def is_active_hour(self) -> bool:
        current = datetime.now().time()
        active_hours = self.config.ACTIVE_HOURS

        logging.info(f"Checking active hours. Current time: {current}")
        logging.debug(f"Full active hours config: {active_hours}")
        logging.debug(f"Is weekend? {self.weekend}")

        if self.weekend:
            weekend = active_hours['weekend']
            start = datetime.strptime(weekend['start'], "%H:%M").time()
            end = datetime.strptime(weekend['end'], "%H:%M").time()
            is_active = start <= current <= end

            logging.info(f"Weekend schedule - Start: {start}, End: {end}")
            logging.info(
                f"Current time {current} is {'within' if is_active else 'outside'} weekend active hours"
            )
            return is_active

        weekday = active_hours['weekday']
        logging.debug(f"Weekday schedule: {weekday}")

        morning_start = datetime.strptime(weekday['morning']['start'], "%H:%M").time()
        morning_end = datetime.strptime(weekday['morning']['end'], "%H:%M").time()
        lunch_start = datetime.strptime(weekday['lunch']['start'], "%H:%M").time()
        lunch_end = datetime.strptime(weekday['lunch']['end'], "%H:%M").time()
        evening_start = datetime.strptime(weekday['evening']['start'], "%H:%M").time()
        evening_end = datetime.strptime(weekday['evening']['end'], "%H:%M").time()

        logging.info(
            f"""
        Checking against weekday schedules:
        Morning: {morning_start} - {morning_end}
        Lunch:   {lunch_start} - {lunch_end}
        Evening: {evening_start} - {evening_end}
        Current: {current}
        """
        )

        is_morning = morning_start <= current <= morning_end
        is_lunch = lunch_start <= current <= lunch_end
        is_evening = evening_start <= current <= evening_end

        logging.debug(
            f"Time period checks - Morning: {is_morning}, Lunch: {is_lunch}, Evening: {is_evening}"
        )

        is_active = is_morning or is_lunch or is_evening
        logging.info(
            f"Current time {current} is {'within' if is_active else 'outside'} active hours"
        )

        return is_active

    def enforce_action_delay(self):
        logging.info("Enforcing action delay")
        elapsed = (datetime.now() - self.last_action_time).total_seconds()
        logging.debug(f"Time elapsed since last action: {elapsed} seconds")

        if elapsed < 30:
            delay = 30 - elapsed
            logging.info(f"Enforcing delay of {delay} seconds")
            time_module.sleep(delay)

        self.last_action_time = datetime.now()
        logging.debug(f"Updated last action time to: {self.last_action_time}")

    def execute_cycle(self, session: InstaPy) -> None:
        logging.info("Starting execution cycle")
        actions = self._get_actions(session)
        logging.debug(f"Retrieved {len(actions)} possible actions")

        random.shuffle(actions)
        logging.info("Actions shuffled randomly")

        for action in actions:
            logging.info(f"Executing action: {action.__name__}")
            with self.error_handling(action.__name__):
                action()
                logging.info(f"Action {action.__name__} completed successfully")

                self.enforce_action_delay()
                sleep_time = random.randint(30, 180)
                logging.info(f"Sleeping for {sleep_time} seconds between actions")
                time_module.sleep(sleep_time)

    def get_targets(self, type_: str, count: int) -> List[str]:
        sources = {
            'hashtags': [tag for tags in self.config.HASHTAGS.values() for tag in tags],
            'accounts': self.config.TARGET_ACCOUNTS,
            'locations': self.config.LOCATIONS,
        }
        logging.info(f"Getting {count} {type_} targets")
        return random.sample(sources[type_], min(count, len(sources[type_])))

    def _get_actions(self, session: InstaPy) -> List[Callable]:
        logging.info("Getting list of actions for current session")
        settings = self.get_session_settings()
        logging.debug(f"Session settings: {settings}")

        def interact_feed():
            logging.info("Setting up feed interaction")
            session.set_do_like(enabled=True, percentage=70)
            session.set_do_comment(enabled=True, percentage=20)
            amount = min(
                random.randint(5, 15),
                self.config.MAX_DAILY_INTERACTIONS - self.daily_interactions,
            )
            logging.info(f"Interacting with feed, amount: {amount}")
            session.like_by_feed(
                amount=amount,
                randomize=True,
                unfollow=False,
                interact=True,
            )

        def engage_location():
            logging.info("Setting up location engagement")
            locations = self.get_targets('locations', 2)
            if not locations:
                logging.warning("No locations available for engagement")
                return
            logging.debug(f"Selected locations: {locations}")
            amount = min(
                random.randint(4, 8),
                self.config.MAX_DAILY_INTERACTIONS - self.daily_interactions,
            )
            skip_top = random.choice([True, False])
            logging.info(
                f"Engaging with locations, amount: {amount}, skip_top: {skip_top}"
            )
            session.like_by_locations(
                locations=locations,
                amount=amount,
                skip_top_posts=skip_top,
            )

        def engage_hashtags():
            logging.info("Setting up hashtag engagement")
            hashtags = self.get_targets('hashtags', 3)
            if not hashtags:
                logging.warning("No hashtags available for engagement")
                return
            logging.debug(f"Selected hashtags: {hashtags}")
            amount = min(
                random.randint(5, 10),
                self.config.MAX_DAILY_INTERACTIONS - self.daily_interactions,
            )
            logging.info(f"Engaging with hashtags, amount: {amount}")
            session.like_by_tags(
                tags=hashtags,
                amount=amount,
                interact=True,
                randomize=True,
            )

        def engage_users():
            logging.info("Setting up user engagement")
            accounts = self.get_targets('accounts', 2)
            if not accounts:
                logging.warning("No accounts available for engagement")
                return
            logging.debug(f"Selected accounts: {accounts}")
            amount = min(
                random.randint(5, 8),
                self.config.MAX_DAILY_INTERACTIONS - self.daily_interactions,
            )
            delay = random.randint(60, 120)
            logging.info(f"Engaging with users, amount: {amount}, delay: {delay}")
            session.follow_user_followers(
                usernames=accounts,
                amount=amount,
                randomize=True,
                interact=True,
                sleep_delay=delay,
            )

        def unfollow():
            logging.info("Setting up unfollow action")
            amount = min(
                random.randint(10, 15),
                self.config.MAX_DAILY_INTERACTIONS - self.daily_interactions,
            )
            non_followers = random.choice([True, False])
            delay = random.randint(450, 600)
            logging.info(
                f"Unfollowing users, amount: {amount}, "
                f"non_followers: {non_followers}, "
                f"delay: {delay}"
            )
            session.unfollow_users(
                amount=amount,
                nonFollowers=non_followers,
                style="RANDOM",
                unfollow_after=48 * 60 * 60,
                sleep_delay=delay,
            )

        actions = [interact_feed]
        logging.debug("Added base action: interact_feed")

        remaining_interactions = (
            self.config.MAX_DAILY_INTERACTIONS - self.daily_interactions
        )
        logging.info(f"Remaining interactions: {remaining_interactions}")

        if remaining_interactions <= 0:
            logging.warning("No remaining interactions available")
            return []

        if settings['mode'] == "active":
            logging.info("Adding active mode actions")
            actions.extend([engage_location, engage_hashtags, engage_users])
        elif settings['mode'] == "normal":
            logging.info("Adding normal mode actions")
            actions.extend([engage_hashtags, engage_users])

        current_hour = datetime.now().hour
        if current_hour in [10, 14, 18, 21]:
            logging.info(f"Adding unfollow action for hour {current_hour}")
            actions.append(unfollow)

        logging.info(f"Final action list contains {len(actions)} actions")
        return actions

    def get_break_duration(self) -> Optional[int]:
        current = datetime.now().time()
        breaks_config = self.config.BREAKS

        lunch_end = (
            datetime.combine(datetime.today(), self.breaks['lunch'])
            + timedelta(minutes=random.randint(30, 60))
        ).time()
        if self.breaks['lunch'] <= current <= lunch_end:
            logging.info("Taking a lunch break")
            return random.randint(
                breaks_config['lunch']['duration']['min'],
                breaks_config['lunch']['duration']['max'],
            )

        for break_time in self.breaks['bathroom']:
            break_end = (
                datetime.combine(datetime.today(), break_time) + timedelta(minutes=10)
            ).time()
            if break_time <= current <= break_end:
                logging.info("Taking a bathroom break")
                return random.randint(
                    breaks_config['bathroom']['duration']['min'],
                    breaks_config['bathroom']['duration']['max'],
                )
        return None

    def get_session_settings(self) -> Dict:
        current_hour = datetime.now().hour
        if 22 <= current_hour or current_hour < 6:
            mode = "sleepy"
        elif current_hour in [12, 13, 19, 20, 21]:
            mode = "active"
        else:
            mode = "normal"

        limits = self.config.HOURLY_LIMITS[mode]
        if self.weekend:
            limits = {k: int(v * 1.5) for k, v in limits.items()}

        logging.info(f"Running in {mode} mode with limits: {limits}")
        return {'mode': mode, 'limits': limits}

    def init_session(self) -> InstaPy:
        session = InstaPy(
            username=self.config.USERNAME,
            password=self.config.PASSWORD,
            headless_browser=True,
            geckodriver_path=GeckoDriverManager().install(),
            want_check_browser=False,
            disable_image_load=True,
            page_delay=10,
            bypass_security_challenge_using="email",
        )

        settings = self.get_session_settings()
        limits = settings['limits']

        session.set_quota_supervisor(
            enabled=True,
            peak_follows_hourly=limits["follows"],
            peak_follows_daily=limits["follows"] * 24,
            peak_unfollows_hourly=limits["unfollows"],
            peak_unfollows_daily=limits["unfollows"] * 24,
            peak_likes_hourly=limits["likes"],
            peak_likes_daily=limits["likes"] * 24,
            peak_comments_hourly=limits["comments"],
            peak_comments_daily=limits["comments"] * 24,
            sleep_after=["follows", "unfollows", "likes", "comments"],
        )

        bounds = self.config.RELATIONSHIP_BOUNDS
        session.set_relationship_bounds(
            enabled=True,
            max_followers=bounds['max_followers'],
            min_followers=bounds['min_followers'],
            min_following=bounds['min_following'],
            min_posts=bounds['min_posts'],
            max_following=bounds['max_following'],
            max_posts=bounds['max_posts'],
        )

        session.set_skip_users(
            skip_private=True, skip_no_profile_pic=True, skip_business=True
        )

        session.set_user_interact(
            amount=random.randint(3, 6), randomize=True, percentage=70
        )

        logging.info(f"Session initialized with settings: {settings}")
        return session

    def run(self):
        logging.info("Starting bot run loop")
        retry_count = 0
        max_retries = 3

        while True:
            try:
                if self.daily_interactions >= self.config.MAX_DAILY_INTERACTIONS:
                    logging.warning("Daily interaction limit reached")
                    logging.info("Sleeping for 24 hours")
                    time_module.sleep(24 * 3600)
                    self.daily_interactions = 0
                    logging.info("Reset daily interactions counter")
                    continue

                if not self.is_active_hour():
                    sleep_time = random.randint(1800, 3600)
                    logging.info(
                        f"Not active hour, sleeping for {sleep_time / 60:.1f} minutes"
                    )
                    time_module.sleep(sleep_time)
                    continue

                break_time = self.get_break_duration()
                if break_time:
                    logging.info(f"Taking a break for {break_time / 60:.1f} minutes")
                    time_module.sleep(break_time)
                    continue

                logging.info("Initializing new session")
                self.session = self.init_session()

                with smart_run(self.session):
                    cycles = random.randint(2, 4)
                    logging.info(f"Running {cycles} cycles")

                    for cycle_num in range(cycles):
                        logging.info(f"Starting cycle {cycle_num + 1}/{cycles}")
                        self.execute_cycle(self.session)
                        sleep_time = random.randint(180, 600)
                        logging.info(
                            f"Sleeping for {sleep_time / 60:.1f} minutes between cycles"
                        )
                        time_module.sleep(sleep_time)

                    interaction_increment = random.randint(5, 15)
                    self.daily_interactions += interaction_increment
                    logging.info(
                        f"Incremented daily interactions by {interaction_increment}"
                    )
                    logging.info(f"Total daily interactions: {self.daily_interactions}")

                retry_count = 0
                time_sleep = random.randint(900, 1800)
                logging.info(
                    f"Sleeping for {time_sleep / 60:.1f} minutes after successful session"
                )
                time_module.sleep(time_sleep)

            except (WebDriverException, TimeoutException) as e:
                logging.error(f"Browser error encountered: {str(e)}", exc_info=True)
                retry_count += 1
                logging.warning(f"Retry attempt {retry_count}/{max_retries}")
                if retry_count >= max_retries:
                    error_msg = "Maximum retries reached"
                    logging.critical(error_msg)
                    raise RuntimeError(error_msg)
                logging.info("Sleeping for 15 minutes before retry")
                time_module.sleep(900)
            except RuntimeError as e:
                logging.error(f"Runtime error encountered: {str(e)}", exc_info=True)
                retry_count += 1
                logging.warning(f"Retry attempt {retry_count}/{max_retries}")
                if retry_count >= max_retries:
                    logging.critical("Maximum retries reached")
                    raise
                logging.info("Sleeping for 5 minutes before retry")
                time_module.sleep(300)


if __name__ == "__main__":
    logging.info("Starting bot")
    bot = InstagramBot()
    bot.run()

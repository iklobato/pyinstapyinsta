import logging
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional
import random
import time as time_module

import pytz
import yaml

from instapy.xpath_compile import xpath
from webdriver_manager.firefox import GeckoDriverManager
from instapy import InstaPy, smart_run

datetime.now(pytz.timezone('America/Sao_Paulo'))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("instabot.log"), logging.StreamHandler()],
)

# Monkey patch to fix error with login element not found
# https://stackoverflow.com/questions/75662587/instapy-selenium-common-exceptions-nosuchelementexception-message-unable-to-l
xpath["login_user"] = {"login_elem_no_such_exception_2", "//div[text()='Log In']"}


class Config:
    def __init__(self, config_path: str = 'config.yaml'):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.USERNAME = config['auth']['credentials']['username']
        self.PASSWORD = config['auth']['credentials']['password']
        self.MAX_DAILY_INTERACTIONS = config['limits']['interactions']['max_daily']
        self.LOCATIONS = config['targeting']['locations']
        self.HASHTAGS = config['targeting']['hashtags']
        self.TARGET_ACCOUNTS = config['targeting']['accounts']
        self.HOURLY_LIMITS = config['engagement']['hourly_limits']
        self.ACTIVE_HOURS = config['schedule']['active_hours']
        self.BREAKS = config['schedule']['breaks']
        self.RELATIONSHIP_BOUNDS = config['limits']['relationship_bounds']


class InstagramBot:
    def __init__(self, config_path: str = 'config.yml'):
        self.config = Config(config_path)
        self.daily_interactions = 0
        self.weekend = datetime.now().weekday() >= 5
        self._init_schedule()

    def _init_schedule(self):
        breaks_config = self.config.BREAKS
        self.breaks = {
            'bathroom': [
                time(
                    random.randint(
                        breaks_config['bathroom']['morning']['hour_start'],
                        breaks_config['bathroom']['morning']['hour_end'],
                    ),
                    random.randint(0, 59),
                ),
                time(
                    random.randint(
                        breaks_config['bathroom']['afternoon']['hour_start'],
                        breaks_config['bathroom']['afternoon']['hour_end'],
                    ),
                    random.randint(0, 59),
                ),
                time(
                    random.randint(
                        breaks_config['bathroom']['evening']['hour_start'],
                        breaks_config['bathroom']['evening']['hour_end'],
                    ),
                    random.randint(0, 59),
                ),
            ],
            'lunch': time(
                random.randint(
                    breaks_config['lunch']['hour_start'],
                    breaks_config['lunch']['hour_end'],
                ),
                random.randint(0, 59),
            ),
        }

    def is_active_hour(self) -> bool:
        current = datetime.now().time()
        active_hours = self.config.ACTIVE_HOURS

        if self.weekend:
            weekend = active_hours['weekend']
            start = datetime.strptime(weekend['start'], "%H:%M").time()
            end = datetime.strptime(weekend['end'], "%H:%M").time()
            return start <= current <= end

        weekday = active_hours['weekday']
        morning_start = datetime.strptime(weekday['morning']['start'], "%H:%M").time()
        morning_end = datetime.strptime(weekday['morning']['end'], "%H:%M").time()
        lunch_start = datetime.strptime(weekday['lunch']['start'], "%H:%M").time()
        lunch_end = datetime.strptime(weekday['lunch']['end'], "%H:%M").time()
        evening_start = datetime.strptime(weekday['evening']['start'], "%H:%M").time()
        evening_end = datetime.strptime(weekday['evening']['end'], "%H:%M").time()

        return (
            morning_start <= current <= morning_end
            or lunch_start <= current <= lunch_end
            or evening_start <= current <= evening_end
        )

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

    def get_targets(self, type_: str, count: int) -> List[str]:
        sources = {
            'hashtags': [tag for tags in self.config.HASHTAGS.values() for tag in tags],
            'accounts': self.config.TARGET_ACCOUNTS,
            'locations': self.config.LOCATIONS,
        }
        logging.info(f"Getting {count} {type_} targets")
        return random.sample(sources[type_], min(count, len(sources[type_])))

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

    def execute_cycle(self, session: InstaPy) -> None:
        actions = self._get_actions(session)
        random.shuffle(actions)

        for action in actions:
            try:
                action()
                logging.info(f"Action {action} completed")
                time_module.sleep(random.randint(30, 180))
            except Exception as e:
                logging.info(f"Error in action: {str(e)}")
                continue

    def _get_actions(self, session: InstaPy) -> List:
        settings = self.get_session_settings()

        def interact_feed():
            session.set_do_like(enabled=True, percentage=70)
            session.set_do_comment(enabled=True, percentage=20)
            session.like_by_feed(
                amount=random.randint(5, 15),
                randomize=True,
                unfollow=False,
                interact=True,
            )

            if random.random() < 0.3:
                session.interact_user_likers(
                    usernames=self.get_targets('accounts', 1),
                    posts_grab_amount=random.randint(1, 3),
                )

        def engage_location():
            locations = self.get_targets('locations', 2)
            session.like_by_locations(
                locations=locations,
                amount=random.randint(4, 8),
                skip_top_posts=random.choice([True, False]),
            )
            if random.random() < 0.7:
                session.follow_by_locations(
                    locations=locations, amount=random.randint(3, 6)
                )

        def engage_hashtags():
            hashtags = self.get_targets('hashtags', 3)
            session.like_by_tags(
                tags=hashtags,
                amount=random.randint(5, 10),
                interact=True,
                randomize=True,
            )
            if random.random() < 0.6:
                session.follow_by_tags(
                    tags=hashtags, amount=random.randint(4, 7), interact=True
                )

        def engage_users():
            accounts = self.get_targets('accounts', 2)
            if random.random() < 0.7:
                session.follow_user_followers(
                    usernames=accounts,
                    amount=random.randint(5, 8),
                    randomize=True,
                    interact=True,
                    sleep_delay=random.randint(60, 120),
                )
            else:
                session.interact_user_followers(
                    usernames=accounts, amount=random.randint(3, 6), randomize=True
                )

        def unfollow():
            session.unfollow_users(
                amount=random.randint(10, 15),
                nonFollowers=random.choice([True, False]),
                style="RANDOM",
                unfollow_after=48 * 60 * 60,
                sleep_delay=random.randint(450, 600),
            )

        actions = [interact_feed]

        if settings['mode'] == "active":
            actions.extend([engage_location, engage_hashtags, engage_users])
        elif settings['mode'] == "normal":
            actions.extend([engage_hashtags, engage_users])

        if datetime.now().hour in [10, 14, 18, 21]:
            actions.append(unfollow)

        logging.info(f"Actions for this cycle: {actions}")
        return actions

    def run(self):
        while True:
            if self.daily_interactions >= self.config.MAX_DAILY_INTERACTIONS:
                logging.info("Daily limit reached, resting until tomorrow")
                time_module.sleep(24 * 3600)
                self.daily_interactions = 0
                continue

            if not self.is_active_hour():
                time_module.sleep(random.randint(1800, 3600))
                continue

            break_time = self.get_break_duration()
            if break_time:
                logging.info(f"Taking a break for {break_time / 60:.1f} minutes")
                time_module.sleep(break_time)
                continue

            session = self.init_session()

            with smart_run(session):
                for _ in range(random.randint(2, 4)):
                    self.execute_cycle(session)
                    time_module.sleep(random.randint(180, 600))
                self.daily_interactions += random.randint(5, 15)

            time_module.sleep(random.randint(900, 1800))


if __name__ == "__main__":
    logging.info("Starting bot")
    bot = InstagramBot()
    bot.run()

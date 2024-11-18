import os
import logging
from base64 import b64decode

from instapy import InstaPy, smart_run
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional
import random
import time as time_module

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("instabot.log"), logging.StreamHandler()],
)


class Config:
    USERNAME = b64decode(os.getenv('INSTA_USER')).decode()
    PASSWORD = b64decode(os.getenv('INSTA_PASS')).decode()
    MAX_DAILY_INTERACTIONS = 200

    LOCATIONS = [
        '213829509/sao-paulo-brazil/',
        '213670729/rio-de-janeiro-brazil/',
        '214494743/curitiba-parana/',
        '213949389/campinas-sao-paulo/',
        '259203564/itatiba/',
        '488871860/valinhos-sao-paulo/',
    ]

    HASHTAGS = {
        'work': ['marketingdigitalbrasil', 'marketingbrasil', 'empreendedorismobrasil'],
        'interest': ['fotografiabrasil', 'designgrafico', 'publicidade'],
        'lifestyle': [
            'vidadeempreendedor',
            'lifestyleempreendedor',
            'mindsetempreendedor',
        ],
    }

    TARGET_ACCOUNTS = [
        'rdstation',
        'resultadosdigitais',
        'rockcontent',
        'neilpatel',
        'exame',
    ]

    HOURLY_LIMITS = {
        "sleepy": {"follows": 3, "unfollows": 2, "likes": 8, "comments": 1},
        "normal": {"follows": 5, "unfollows": 4, "likes": 12, "comments": 2},
        "active": {"follows": 8, "unfollows": 6, "likes": 20, "comments": 4},
    }


class InstagramBot:
    def __init__(self):
        self.config = Config()
        self.daily_interactions = 0
        self.weekend = datetime.now().weekday() >= 5
        self._init_schedule()

    def _init_schedule(self):
        self.breaks = {
            'bathroom': [
                time(random.randint(10, 11), random.randint(0, 59)),
                time(random.randint(14, 15), random.randint(0, 59)),
                time(random.randint(20, 21), random.randint(0, 59)),
            ],
            'lunch': time(random.randint(12, 13), random.randint(0, 59)),
        }

    def is_active_hour(self) -> bool:
        current = datetime.now().time()
        if self.weekend:
            return time(11, 0) <= current <= time(23, 0)
        return (
                time(8, 30) <= current <= time(10, 30)
                or time(12, 0) <= current <= time(13, 0)
                or time(19, 0) <= current <= time(23, 0)
        )

    def get_break_duration(self) -> Optional[int]:
        current = datetime.now().time()

        # Lunch break
        lunch_end = (
                datetime.combine(datetime.today(), self.breaks['lunch'])
                + timedelta(minutes=random.randint(30, 60))
        ).time()
        if self.breaks['lunch'] <= current <= lunch_end:
            return random.randint(1800, 3600)

        # Bathroom breaks
        for break_time in self.breaks['bathroom']:
            break_end = (
                    datetime.combine(datetime.today(), break_time) + timedelta(minutes=10)
            ).time()
            if break_time <= current <= break_end:
                return random.randint(300, 600)
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

        return {'mode': mode, 'limits': limits}

    def get_targets(self, type_: str, count: int) -> List[str]:
        sources = {
            'hashtags': [tag for tags in self.config.HASHTAGS.values() for tag in tags],
            'accounts': self.config.TARGET_ACCOUNTS,
            'locations': self.config.LOCATIONS,
        }
        return random.sample(sources[type_], min(count, len(sources[type_])))

    def init_session(self) -> InstaPy:
        session = InstaPy(
            username=self.config.USERNAME,
            password=self.config.PASSWORD,
            # bypass_suspicious_attempt=True,
            want_check_browser=False,
            disable_image_load=True,
            headless_browser=True,
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

        session.set_relationship_bounds(
            enabled=True,
            max_followers=15000,
            min_followers=1000,
            min_following=500,
            min_posts=20,
            max_following=25000,
            max_posts=1_000,
        )

        session.set_skip_users(
            skip_private=True, skip_no_profile_pic=True, skip_business=True
        )

        session.set_user_interact(
            amount=random.randint(3, 6), randomize=True, percentage=70
        )

        session.set_smart_location_hashtags(
            self.get_targets('locations', 2), radius=50, limit=10
        )

        return session

    def execute_cycle(self, session: InstaPy) -> None:
        actions = self._get_actions(session)
        random.shuffle(actions)

        for action in actions:
            try:
                action()
                time_module.sleep(random.randint(30, 180))
            except Exception as e:
                print(f"Error in action: {str(e)}")
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

        return actions

    def run(self):
        while True:
            try:
                if self.daily_interactions >= self.config.MAX_DAILY_INTERACTIONS:
                    print("Daily limit reached, resting until tomorrow")
                    time_module.sleep(24 * 3600)  # Sleep until tomorrow
                    self.daily_interactions = 0
                    continue

                if not self.is_active_hour():
                    time_module.sleep(random.randint(1800, 3600))
                    continue

                break_time = self.get_break_duration()
                if break_time:
                    print(f"Taking a break for {break_time / 60:.1f} minutes")
                    time_module.sleep(break_time)
                    continue

                session = self.init_session()

                with smart_run(session):
                    for _ in range(random.randint(2, 4)):
                        self.execute_cycle(session)
                        time_module.sleep(random.randint(180, 600))
                    self.daily_interactions += random.randint(5, 15)

                time_module.sleep(random.randint(900, 1800))

            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                time_module.sleep(900)
                continue


if __name__ == "__main__":
    bot = InstagramBot()
    bot.run()
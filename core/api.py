import re
from datetime import datetime

import requests
from munch import Munch

re_date = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def parse_data(obj, key=None):
    if isinstance(obj, dict):
        return {k: parse_data(v, key=k) for k, v in obj.items()}
    if isinstance(obj, list):
        return tuple(parse_data(v) for v in obj)
    if not isinstance(obj, str):
        return obj
    if re_date.match(obj):
        obj = datetime.strptime(obj, '%Y-%m-%dT%H:%M:%SZ')
    return obj


class Api:
    def __init__(self):
        self.url = Munch(
            times="https://api.transit.welbits.com/stops/times/",
            card="https://api.transit.welbits.com/cards/"
        )

    def get(self, url, *args, **kvargs):
        if kvargs:
            r = requests.post(url, data=kvargs)
        else:
            r = requests.get(url)
        data = r.json()
        data = parse_data(data)
        return Munch.fromDict(data)

    def get_times(self, id):
        return self.get(self.url.times + str(id))

    def get_card(self, card):
        return self.get(self.url.card + str(card))


if __name__ == "__main__":
    import sys
    a = Api()
    print(a.get_card(sys.argv[1]))

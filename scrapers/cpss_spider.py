from scrapy import Spider, Request
import json


class SaskSpider(Spider):
    name = "SaskRXValidator_Spider"
    API_URL = "https://www.cps.sk.ca/CPSSWebApi/api/Physicians/"

    def __init__(self, first_name, last_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.first_name = first_name
        self.last_name = last_name

    def build_query(self) -> str:
        first_name, last_name = [_.replace(" ", "+")
                                 for _ in [self.first_name, self.last_name]]
        return f'{self.API_URL}?name={first_name}+{last_name}'

    def get_verification_filter(self):
        return lambda item: item['FirstName'] == self.first_name and \
            (item['LastName'] == self.last_name or self.last_name == None)

    def start_requests(self):
        for userdata in self.user_info:
            payload = {"userdata": userdata}
            req = self.build_query(payload)
            yield Request(url=req, callback=self.parse, meta=payload)

    def on_error(self, failure):
        # print("Error: ", failure)
        yield {"status": "FAILED"}

    def parse(self, response):
        if not response.status == 200:
            return self.on_error(response)
        result = list(filter(self.get_verification_filter,
                             json.loads(response.body)))

        if len(result) == 0:
            # print("Invalid or name not in registry.")
            yield {"status": "FAILED"}
        # elif len(result) > 1:
            # print("Duplicate or several results found.")

        # print(f"Result for {self.first_name} {self.last_name}")
        yield {"status": ["INACTIVE", "VERIFIED"][result[0]['Status'] == 'A']}

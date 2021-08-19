import time
import random
import requests
import pandas as pd

from scrapy.selector import Selector


class SteamReviewCollector:

    def __init__(self):
        self.headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
            'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
            'X-Prototype-Version': '1.7',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            # 'Referer': 'https://steamcommunity.com/app/42960/reviews/?browsefilter=trendsixmonths&snr=1_5_100010_&p=1&filterLanguage=english',
            'Accept-Language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,uk;q=0.6,en-GB;q=0.5',
        }

    def collect(self, app_id):
        print(f'Running for game - {app_id}')
        url = f'https://steamcommunity.com/app/{app_id}/reviews/?browsefilter=trendsixmonths&snr=1_5_100010_&p=1&filterLanguage=english'

        response = requests.get(
            url,
            headers=self.headers,
        )

        res = Selector(text=response.content.decode())
        cards = res.css('div.apphub_Card')

        form = res.xpath("//form[contains(@id, 'MoreContentForm')]")

        reviews = pd.DataFrame()

        reviews = self.parse_cards(cards=cards, reviews=reviews)

        while cards:
            page = form.css('input[name="p"]::attr(value)').get()
            print(f'Running for game {app_id}, page {page}')
            params = {
                'userreviewscursor': form.css('input[name="userreviewscursor"]::attr(value)').get(),
                'userreviewsoffset': form.css('input[name="userreviewsoffset"]::attr(value)').get(),
                'p': form.css('input[name="p"]::attr(value)').get(),
                'workshopitemspage': form.css('input[name="workshopitemspage"]::attr(value)').get(),
                'readytouseitemspage': form.css('input[name="readytouseitemspage"]::attr(value)').get(),
                'mtxitemspage': form.css('input[name="mtxitemspage"]::attr(value)').get(),
                'itemspage': form.css('input[name="itemspage"]::attr(value)').get(),
                'screenshotspage': form.css('input[name="screenshotspage"]::attr(value)').get(),
                'videospage': form.css('input[name="videospage"]::attr(value)').get(),
                'artpage': form.css('input[name="artpage"]::attr(value)').get(),
                'allguidepage': form.css('input[name="allguidepage"]::attr(value)').get(),
                'webguidepage': form.css('input[name="webguidepage"]::attr(value)').get(),
                'integratedguidepage': form.css('input[name="integratedguidepage"]::attr(value)').get(),
                'discussionspage': form.css('input[name="discussionspage"]::attr(value)').get(),
                'numperpage': form.css('input[name="numperpage"]::attr(value)').get(),
                'browsefilter': ['trendsixmonths', 'trendsixmonths'],
                'appid': str(app_id),
                'appHubSubSection': ['10', '10'],
                'l': 'english',
                'filterLanguage': 'english',
                'searchText': '',
                'maxInappropriateScore': form.css('input[name="maxInappropriateScore"]::attr(value)').get(),

            }

            response = requests.get(
                f'https://steamcommunity.com/app/{app_id}/homecontent/',
                headers=self.headers,
                params=params
            )

            res = Selector(text=response.content.decode())
            cards = res.css('div.apphub_Card')

            form = res.xpath("//form[contains(@id, 'MoreContentForm')]")

            reviews = self.parse_cards(cards=cards, reviews=reviews)

            sleep_time = random.uniform(0.3, 1.5)
            print(f'Currently collected {len(reviews)}, reviews!')
            print(f'Sleep for {sleep_time} sec.')
            time.sleep(sleep_time)

        reviews.to_csv(
                f'reviews_{app_id}.csv',
                sep=',',
                columns=[
                    'SteamId', 'ProfileURL', 'ReviewText', 'Review',
                    'ReviewLength', 'PlayHours', 'DatePosted'
                ]
            )

    def parse_cards(self, cards, reviews):
        for card in cards:
            profile_url = card.css('div.apphub_CardContentAuthorName > a::attr(href)').get()

            # steam id
            try:
                steam_id = profile_url.split('/')[-2]
            except:
                print('There is no profile_url found')
                steam_id = ''

            # # check to see if I've already collected this review
            # if steam_id in review_ids:
            #     continue
            # else:
            #     review_ids.add(steam_id)

            # username
            user_name = card.xpath('.//div[@class="apphub_friend_block"]/div/a[2]/text()').get()

            # language of the review
            date_posted = card.xpath('.//div[@class="apphub_CardTextContent"]/div/text()').get()
            review_content = card.xpath('.//div[@class="apphub_CardTextContent"]//text()').getall()
            review_content = ' '.join([rc.strip() for rc in review_content if rc.strip()])

            review_content = review_content.replace(date_posted.strip(), '').strip()

            # review length
            review_length = len(review_content.replace(' ', ''))

            # recommendation
            thumb_text = card.xpath('.//div[@class="reviewInfo"]/div[2]/text()').get()

            # amount of play hours
            play_hours = card.xpath('.//div[@class="reviewInfo"]/div[3]/text()').get()
            # save review
            review = {
                'SteamId': steam_id,
                'ProfileURL': profile_url,
                'ReviewText': review_content,
                'Review': thumb_text,
                'ReviewLength': review_length,
                'PlayHours': play_hours,
                'DatePosted': date_posted
            }
            reviews = reviews.append(review, ignore_index=True)

        return reviews


if __name__ == '__main__':
    collector = SteamReviewCollector()

    app_id = 42960
    for app_id in [203770, 394360, 281990, 42960]:
        collector.collect(app_id)
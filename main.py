#!/usr/bin/python2.7
from urllib import unquote
import requests
import m3u8
import subprocess
import re
import os

base_m3u_link = "https://pbtv.scaleengine.net/pbtv-vod/play/sestore3/pbtv/"
useragent = "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0"

# Change these values
email = ""
password = ""


def pretty_name(old_name):
    new_name = unquote(old_name)
    new_name = old_name.replace(" ", ".").replace("#", ".").replace("!", ".").replace("?'", ".").replace(":", ".").replace(",", ".").replace("\\", ".").replace("/", ".").replace("<", ".").replace(">", ".").replace("|", ".").replace("&", ".").replace("@", ".").replace("*", ".").replace("$", ".").replace("#", "").replace("amp;A", "and")
    return new_name


class Powerbomb:

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.cookies = None
        self.logged_in = False

    def login(self):
        with requests.Session() as s:
            # Get the login page and the hidden login token
            loginPage = s.get("https://powerbomb.tv/login")
            loginToken = loginPage.text.split('<input type="hidden" name="_token" value="')[1].split('">')[0]

            # Set the form details and login
            auth_values = {'email': self.email,
                           'password': self.password,
                            '_token': loginToken}
            s.post("https://powerbomb.tv/login", auth_values)

            # We're in ! Print a message saying so
            self.cookies = s.cookies
            self.logged_in = True

            print("Logged in!")

    def get_video(self, video_id, promotion):
        # If we aren't logged in, log in
        if not self.logged_in:
            self.login()
        with requests.Session() as s:
            # Get the cookies and remove the html encoding
            s.cookies = self.cookies
            cookies_string = ';'.join([x + '=' + y for x, y in self.cookies.items()])
            cookies_string = unquote(cookies_string)

            # Get the event page and copy the key/pass combo + the event details
            response = s.get("https://powerbomb.tv/player/"+video_id)
            eventSlug = response.text.split("var eventSlug = '")[1].split("'")[0]
            eventTitle = response.text.split("var eventTitle = '")[1].split("'")[0]
            sevuKey = unquote(response.text.split("var sevuKey = '")[1].split("'")[0])
            sevuPass = unquote(response.text.split("var sevuPass = '")[1].split("'")[0])

            # Convert the above into a readable filename
            output_name = "{}-{}".format(eventSlug, eventTitle)
            output_name = pretty_name(output_name)

            # Check if a folder for the promotion exists
            if not os.path.isdir(promotion):
                os.makedirs(promotion)

            # Get the m3u8 link from the event page.
            m3ulink = base_m3u_link + "{}/{}.smil/playlist.m3u8?key={}&pass={}".format(eventSlug, eventSlug, sevuKey, sevuPass)
            m3u_obj = m3u8.load(m3ulink)

            # Get the highest bitrate option (the first URI) from the m3u8 file above
            stream_url = base_m3u_link +"{}/{}.smil/{}".format(eventSlug, eventSlug, m3u_obj.playlists[0].uri)
            subprocess.call('ffmpeg -user_agent "{}" -headers "Cookie: {}" -i "{}" -c copy {}/"{}".mp4 -y'.format(useragent, cookies_string, stream_url, promotion, output_name), shell=True)


pbomb = Powerbomb(email, password)

pbomb.login()

# Get the promotion and add it to an array called promotion
promotion = []
s = requests.get("https://powerbomb.tv/promotions/")
result = re.findall('<a data-par="#promotion-preview-(.*)" class="promotion-preview-lnk"', s.text)
for key in result:
    promotion.append(key)

# For each promotion get the video
for key in promotion:
    if key == "fresh":
        continue
    else:
        s = requests.get("https://powerbomb.tv/promotion/"+key)
        result = re.findall('id="event-preview-(.*)" data-eventhash="', s.text)
        for intro in result:
           pbomb.get_video(intro, key)

s = requests.get("https://powerbomb.tv/promotion/"+key)
result = re.findall('id="event-preview-(.*)" data-eventhash="', s.text)
for intro in result:
    pbomb.get_video(intro, key)

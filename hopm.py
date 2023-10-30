import irc.bot
import irc.strings
import requests
import logging
import re
import uuid

class ProxyCheckBot(irc.bot.SingleServerIRCBot):
    def __init__(self, server, port, nickname, channel, oper_username, oper_password):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.oper_username = oper_username
        self.oper_password = oper_password

    def on_welcome(self, connection, event):
        # Oper up using provided username and password
        connection.oper(self.oper_username, self.oper_password)
        connection.join(self.channel)

    def on_privnotice(self, connection, event):
        message = event.arguments[0]
        ip_address, nick = self.extract_ip_and_nick_from_privnotice(message)
        
        if ip_address and self.is_proxy(ip_address):
            uid = self.generate_uid()
            self.zline_ip(connection, ip_address, uid)
            connection.send_raw(f"SNOTICEALL \x033[info]\x03 Hopm detected user -{nick}- Using a banned TOR exit node and user got Z-lined. If this is an error, please email admin@elsit.io (ID: {uid})")

    def extract_ip_and_nick_from_privnotice(self, message):
        # Extracting IP and nickname using regex from the privnotice message
        match = re.search(r"Accepted connection from (.*?)@\[([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\]", message)
        return (match.group(2), match.group(1)) if match else (None, None)

    def is_proxy(self, ip_address):
        # Use the proxy checking API
        url = f"http://api.isproxyip.com/v1/check.php"
        params = {
            'key': 'vPpms39j0lGdUsQ7YwOIEB9jzdJTJbiRGr0IRMIIryjoVhWIQe',  # replace with your key
            'ip': ip_address,
            'format': 'json'
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return False
        data = response.json()
        return True if data.get('proxy') else False

    def zline_ip(self, connection, ip_address, uid):
        # ZLINE the IP with the generated UID
        connection.send_raw(f"ZLINE *@{ip_address} 1d :Proxy detected, Z-lined by HOPM (ID: {uid})")

    def generate_uid(self):
        # Generate a short UID
        return str(uuid.uuid4()).split('-')[0].upper()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    bot = ProxyCheckBot("irc.elsit.io", 6667, "HOPM", "#eggdrop", "geo", "cHabQdQux.")
    bot.start()

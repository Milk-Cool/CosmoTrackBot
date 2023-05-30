import os;
import telebot;
import threading;
from http.server import BaseHTTPRequestHandler, HTTPServer;
import json;
from urllib.parse import parse_qs;
from html import unescape;

password = os.environ["PASSWORD"];

f = open("index.html", "r+");
index = f.read();
f.close();

f = open("topics.json", "r");
topics = json.loads(f.read());
f.close();
def commit_topics():
	f = open("topics.json", "w");
	f.write(json.dumps(topics));
	f.close();
	
f = open("names.json", "r");
names = json.loads(f.read());
f.close();
def commit_names():
	f = open("names.json", "w");
	f.write(json.dumps(names));
	f.close();

bot = telebot.TeleBot(os.environ["TOKEN"]);

def server():
	class WebRequestHandler(BaseHTTPRequestHandler):
		def do_GET(self):
			self.send_response(200);
			self.send_header("Content-Type", "text/html");
			self.end_headers();
			self.wfile.write(bytes(index, "ascii"));
			
		def do_POST(self):
			content_length = int(self.headers["Content-Length"]);
			data = parse_qs(self.rfile.read(content_length).decode());
			if(data["password"][0] != password):
				self.send_response(403);
				self.send_header("Content-Type", "text/plain");
				self.end_headers();
				self.wfile.write(b"Wrong password.");
				return;
			if(self.path == "/new"):
				try:
					users = topics[data["topic"][0]];
					for i in users:
						bot.send_message(i, "Привет!\nМы выложили новый пост по теме \"" + names[data["topic"][0]] + "\", обязательно посмотри!\n\n" + data["url"][0]);
					self.send_response(200);
					self.send_header("Content-Type", "text/plain");
					self.end_headers();
					self.wfile.write(b"Sent messages!");
				except KeyError:
					self.send_response(400);
					self.send_header("Content-Type", "text/plain");
					self.end_headers();
					self.wfile.write(b"This topic does not exist.");
			elif(self.path == "/newtopic"):
				topics[data["topic"][0]] = [];
				names[data["topic"][0]] = data["topicname"][0];
				commit_topics();
				commit_names();
				self.send_response(400);
				self.send_header("Content-Type", "text/plain");
				self.end_headers();
				self.wfile.write(b"Topic created!");
				
	server = HTTPServer(("", 8080), WebRequestHandler);
	server.serve_forever();
threading.Thread(target=server).start();

@bot.message_handler(commands=["start"])
def send_welcome(message):
	try:
		topic = message.text.split(" ")[1];
		topics[topic] += [message.from_user.id];
		commit_topics();
		bot.reply_to(message, "Успешно подписал тебя на тему " + unescape(names[topic]) + "!");
	except IndexError:
		bot.reply_to(message, "Привет! 👋\nЭтот бот поможет тебе следить за новостями по космосу. Просто нажми на кнопку \"Следить\" под постом на сайте и бот будет присылать тебе новости про определённую миссию, компанию, страну и т. д.");
bot.infinity_polling();

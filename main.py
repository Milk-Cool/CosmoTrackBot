import os;
import telebot;
import threading;
from http.server import BaseHTTPRequestHandler, HTTPServer;
import json;
from urllib.parse import parse_qs;
from html import unescape;
from math import ceil;

password = os.environ["PASSWORD"];

f = open("index.html", "r");
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

pages = {};

bot = telebot.TeleBot(os.environ["TOKEN"]);
no_markup = telebot.types.ReplyKeyboardRemove(selective=False);

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
			if(self.path == "/new" or self.path == "/new/"):
				try:
					users = topics[data["topic"][0]];
					for i in users:
						bot.send_message(i, "Привет!\nМы выложили новый пост по теме \"" + names[data["topic"][0]] + "\", обязательно посмотри!\n\n" + data["url"][0], reply_markup=no_markup);
					self.send_response(200);
					self.send_header("Content-Type", "text/plain");
					self.end_headers();
					self.wfile.write(b"Sent messages!");
				except KeyError:
					self.send_response(400);
					self.send_header("Content-Type", "text/plain");
					self.end_headers();
					self.wfile.write(b"This topic does not exist.");
			elif(self.path == "/newtopic" or self.path == "/newtopic/"):
				topics[data["topic"][0]] = [];
				names[data["topic"][0]] = unescape(data["topicname"][0]);
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
		if(message.from_user.id not in topics[topic]): topics[topic] += [message.from_user.id];
		commit_topics();
		bot.reply_to(message, "Успешно подписал тебя на тему " + names[topic] + "!", reply_markup=no_markup);
	except IndexError:
		bot.reply_to(message, "Привет! 👋\nЭтот бот поможет тебе следить за новостями по космосу. Просто нажми на кнопку \"Следить\" под постом на сайте и бот будет присылать тебе новости про определённую миссию, компанию, страну и т. д.\n\nДля того, чтобы вручную подписаться на какую-то тему, пришли мне имя темы, и я тебе покажу то, на что ты хочешь подписаться.\nТакже можешь использовать команду /topics, чтобы показать список всех тем.", reply_markup=no_markup);
		
def create_pages_markup(page):
	markup = telebot.types.InlineKeyboardMarkup();
	for i, j in list(names.items())[page * 9:(page + 1) * 9]:
		btn = telebot.types.InlineKeyboardButton(j, callback_data=i);
		markup.add(btn);
	btn_prev = telebot.types.InlineKeyboardButton("Назад", callback_data="!prev");
	btn_next = telebot.types.InlineKeyboardButton("Вперёд", callback_data="!next");
	markup.add(btn_prev, btn_next);
	return markup;

@bot.message_handler(commands=["topics"])
def send_topics(message):
	pages[message.from_user.id] = 0;
	markup = create_pages_markup(0);
	bot.reply_to(message, "Выбери тему:", reply_markup=markup);

@bot.message_handler(func=lambda m: True)
def search_topics(message):
	markup = telebot.types.InlineKeyboardMarkup();
	for i, j in names.items():
		if(message.text.lower() in j.lower()):
			btn = telebot.types.InlineKeyboardButton(j, callback_data=i);
			markup.add(btn);
	bot.reply_to(message, "Выбери тему:", reply_markup=markup);

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
	if(call.data == "!prev"):
		if(pages[call.from_user.id] != 0):
			pages[call.from_user.id] -= 1;
			markup = create_pages_markup(pages[call.from_user.id]);
			bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup);
		bot.answer_callback_query(call.id);
		return;
	if(call.data == "!next"):
		if(pages[call.from_user.id] != ceil(len(names) / 9) - 1):
			pages[call.from_user.id] += 1;
			markup = create_pages_markup(pages[call.from_user.id]);
			bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup);
		bot.answer_callback_query(call.id);
		return;
	if(call.from_user.id not in topics[call.data]): topics[call.data] += [call.from_user.id];
	commit_topics();
	bot.send_message(call.from_user.id, "Подписал тебя на тему " + names[call.data] + "!");
	bot.answer_callback_query(call.id);

bot.infinity_polling();

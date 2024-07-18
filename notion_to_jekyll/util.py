import requests
from datetime import datetime
import logging
import sys

from notion_to_jekyll import fs

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def configure_logger():
	handler = logging.StreamHandler(sys.stdout)
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter('%(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	return

NOTION_FOLDER = "notion2md"
ASSETS = "assets"
POSTS = "_posts"

MANAGER = None
PBAR = None

def get_time_since_edit(page):
	# get time when page was last edited
	edited_time = datetime.strptime(page['last_edited_time'], '%Y-%m-%dT%H:%M:%S.%fZ')
	
	time_delta = datetime.now() - edited_time

	return time_delta.total_seconds()

def check_posts(posts, download_all, update_time):
	to_download = []
	current_posts = fs.get_assets_folders()

	updated = []
	new = []

	for (post_id, p) in posts:
		name = p["properties"]["short-name"]["rich_text"][0]["text"]["content"]

		# If all posts should be downloaded
		if download_all:
			to_download += [(post_id, p)]
		else:
			if not name in current_posts:
				new += [name]
				to_download += [(post_id, p)]
			# Default: if the post has been edited in the last 25 hours, download it
			elif get_time_since_edit(p) < update_time:
				updated += [name]
				to_download += [(post_id, p)]

	if download_all:
		logger.info("Downloading all posts.")
	else:
		logger.info(f"Downloading the following posts: {new+updated}")

	return to_download, updated, new

# Send logsnag notification if a new post has been added
def log_new(new, updated, deleted, token):
	def send_notification(event, description, icon, token):
		# Define the endpoint URL
		url = 'https://api.logsnag.com/v1/log'
		token = token

		data = {
			'project': 'obrhubr',
			'channel': 'blog',
			'event': event,
			'description': description,
			'icon': icon,
			'notify': 'true'
		}

		headers = {
			'Authorization': 'Bearer ' + token,
			'Content-Type': 'application/json'  # Assuming you are sending JSON data
		}
		requests.post(url, json=data, headers=headers)
		return

	def log_update(event, description, icon):
		logger.info(f"{icon} {event} - {description}")

		if token != "none":
			send_notification(event, description, icon, token)

		return
	
	logger.info("Finished exporting posts from Notion to Jekyll.")

	for post in new:
		log_update(
			"publish-post",
			f"A new post has been published: {post}.",
			"📫"
		)

	for post in updated:
		log_update(
			"update-post",
			f"A post has been updated: {post}.",
			"✅"
		)

	for post in deleted:
		log_update(
			"delete-post",
			f"A post has been deleted: {post}.",
			"❌"
		)

	return
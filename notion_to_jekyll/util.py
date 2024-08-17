import requests
from datetime import datetime, timezone
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

def get_last_edit_time(page):
	# get time when page was last edited with utc timezone
	return datetime.strptime(page['last_edited_time'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)

def get_last_download_time(page):
	# get time when page was last downloaded
	properties = page['properties']
	if 'last_downloaded' in properties and properties['last_downloaded']['date']:
		return datetime.fromisoformat(properties['last_downloaded']['date']['start'])
	else:
		# If it has not been downloaded yet, set time to 0 to force update
		current_timezone = datetime.now(timezone.utc).astimezone().tzinfo
		return datetime.fromtimestamp(0, tz=current_timezone)

def check_posts(posts, download_all):
	to_download = []
	current_posts = fs.get_assets_folders()

	updated = []
	new = []

	for (post_id, p) in posts:
		name = p["properties"]["short-name"]["rich_text"][0]["text"]["content"]

		# If all posts should be downloaded
		if download_all:
			to_download += [(post_id, p)]
			continue

		# If the post has not been downloaded at all yet
		if not name in current_posts:
			new += [name]
			to_download += [(post_id, p)]
			continue

		# If the post has been updated since it has been last downloaded
		if get_last_edit_time(p) > get_last_download_time(p):
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

		if token:
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
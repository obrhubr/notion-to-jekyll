from notion_client import Client
from datetime import datetime, timezone

from notion_to_jekyll import util

NOTION_CLIENT = None

def fetch_all_posts(notion_token, db_id):
	global NOTION_CLIENT

	# Connect to notion
	util.logger.debug("Connecting to Notion...")
	NOTION_CLIENT = Client(auth=notion_token)

	# Fetch blog posts from DB
	util.logger.debug("Fetching blog posts from Notion...")
	posts = NOTION_CLIENT.databases.query(
		**{
			"database_id": db_id
		}
	)

	return posts

def filter_posts(posts):
	pages = []

	for entry in posts["results"]:
		if entry["properties"]["Blog"]["select"]["name"] == "Publish":
			post_id = entry["id"]
			
			pages += [(post_id, entry)]

	util.logger.info(f"Found {len(pages)} blog posts to publish.")

	return pages

def get_page(page_id):
	global NOTION_CLIENT
	
	# Get all blocks of page
	blocks = NOTION_CLIENT.blocks.children.list(page_id)

	return blocks["results"]

def get_images(page_id):
	blocks = get_page(page_id)

	# Filter out image blocks
	image_blocks = []

	for block in blocks:
		if block["type"] == "image":
			image_blocks += [block]

	return image_blocks

def store_last_updated(updated_posts):
	current_timezone = datetime.now(timezone.utc).astimezone().tzinfo
	
	for post_id, _ in updated_posts:
		# Update the last downloaded value in Notion table
		NOTION_CLIENT.pages.update(
			page_id=post_id, 
			properties={
				"last_downloaded": {
					"date": {
						"start": datetime.now(current_timezone).isoformat()
					}
				}
			}
		)
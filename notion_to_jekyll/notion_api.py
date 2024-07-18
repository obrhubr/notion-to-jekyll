from notion_client import Client

from notion_to_jekyll import util

def fetch_all_posts(notion_token, db_id):
	# Connect to notion
	util.logger.debug("Connecting to Notion...")
	notion = Client(auth=notion_token)

	# Fetch blog posts from DB
	util.logger.debug("Fetching blog posts from Notion...")
	posts = notion.databases.query(
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
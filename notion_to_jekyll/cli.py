import click
import os
from dotenv import load_dotenv
import enlighten

from notion_to_jekyll import fs
from notion_to_jekyll import notion_api
from notion_to_jekyll import post
from notion_to_jekyll import util

@click.command()
@click.option('--notion-token', help="Notion API token.", required=False, type=str)
@click.option('--db-id', help="Notion DB id.", required=False, type=str)
@click.option('--log', help="Log updated posts to Logsnag.", is_flag=True, default=False, type=bool)
@click.option('--assets-folder', help="Folder in which to store assets.", required=False, type=str)
@click.option('--output-folder', help="Folder in which to store the posts.", required=False, type=str)
@click.option('--download-all', is_flag=True, help="Download all posts.", default=False)
@click.option('--download-id', help="Download post with specific id.", default=None, type=str)
@click.option('--use-katex', is_flag=True, help="Use Katex to render math.", default=True, type=bool)
@click.option('--encode-images', is_flag=True, help="Encode all images as jpg.", default=True, type=bool)
@click.option('--rename-images', is_flag=True, help="Rename images to hash of contents.", default=True, type=bool)
@click.option('--dst-extension', help="The image extension to convert to.", default="webp", type=str)
def cli(
	notion_token, db_id, log, 
	assets_folder, output_folder,
	download_all, download_id,
	use_katex, encode_images, rename_images, dst_extension # options for export_page
):
	util.configure_logger()
	util.logger.info("Starting Notion to Jekyll Exporter...")
	
	# If no tokens have been provided as options, load from environment vars
	if not notion_token or not db_id:
		util.logger.info("Loading secrets from the environment variables.")

		load_dotenv(os.path.join(os.getcwd(), ".env"))
		notion_token = os.environ["NOTION_TOKEN"]
		db_id = os.environ["DB_ID"]

	if log:
		log = os.environ["LOGSNAG_TOKEN"]

	# Set dirs
	if assets_folder:
		util.logger.info(f"Set assets directory to {assets_folder}.")
		util.ASSETS = assets_folder
	if output_folder:
		util.logger.info(f"Set output directory to {output_folder}.")
		util.POSTS = output_folder

	# Download the posts
	try:
		fs.setup_folders()

		# Connect to notion
		notion_api.connect(notion_token)

		# Fetch and filter posts
		posts = notion_api.fetch_all_posts(db_id)
		posts = notion_api.filter_posts(posts)

		if download_id:
			to_download, updated, new = util.get_post_id(posts, download_id)
		else:
			to_download, updated, new = util.check_posts(posts, download_all)

		for index, (post_id, p) in enumerate(to_download):
			name = p["properties"]["short-name"]["rich_text"][0]["text"]["content"]

			# Setup loading bar
			util.MANAGER = enlighten.get_manager()
			util.PBAR = util.MANAGER.counter(total=8, desc=f'Exporting post {name}:', unit='steps')

			# Export page to markdown
			util.logger.info(f"{index+1}/{len(to_download)} - Exporting {name} to Jekyll.")
			post.export_page(post_id, p, use_katex, encode_images, rename_images, dst_extension)

		# Delete any posts that have been removed
		deleted = fs.clean_folders(posts)

		# Log updates to logsnag
		util.log_new(new, updated, deleted, log)
		notion_api.store_last_updated(to_download)
	except Exception as e:
		util.logger.error(f"Error occured while exporting posts: {e}...")
		raise e
	finally:
		# If an error occurs, clean up the folders
		fs.clean_up()

	return
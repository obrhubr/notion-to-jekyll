from notion2md.convertor.richtext import richtext_convertor
from notion2md.exporter.block import MarkdownExporter
import shutil
import re
import os
import urllib.request
from urllib.request import urlretrieve
from PIL import Image

from notion_to_jekyll import fs
from notion_to_jekyll import util
from notion_to_jekyll import notion_api

# Download page as markdown file
def download_markdown(post_id):
	util.logger.debug("Exporting page from Notion...")
	MarkdownExporter(
		block_id=post_id,
		output_path=os.path.join(util.NOTION_FOLDER), 
		download=True
	).export()

	return

def rename_post_folder(post_id, short_name, filename):
	util.logger.debug(f"Rename markdown file and folder to filename={filename}")
	os.rename(
		os.path.join(util.NOTION_FOLDER, short_name, post_id + ".md"),
		os.path.join(util.NOTION_FOLDER, short_name, filename + ".md")
	)

	return

def move_assets(short_name):
	# Create asset directory and move all images there
	util.logger.debug("Create asset directory...")
	os.mkdir(os.path.join(util.NOTION_FOLDER, short_name, util.ASSETS))

	util.logger.debug("Moving assets...")
	files = os.walk(os.path.join(util.NOTION_FOLDER, short_name))
	for dirpath, _, filenames in files:
			for filename in filenames:
				# Only move image assets
				if re.search(r"\.(gif|jpe?g|tiff?|png|webp|bmp)$", filename) != None:
					# Check if in assets
					if dirpath[len(dirpath) - 6:] != "assets":
						src = os.path.join(dirpath, filename)
						dst = os.path.join(util.NOTION_FOLDER, short_name, util.ASSETS)

						util.logger.debug(f"Moved file src={src} to dst={dst}")
						shutil.move(src, dst)

	return

def fetch_previewimage(post, short_name):
	# Add preview image
	preview_images = post["properties"]["preview-image"]["files"]

	# If there is no preview image, return none
	if len(preview_images) == 0:
		return None
	
	# add image to meta tags
	image = preview_images[0]
	name = image['name'].split(".")
	previewimage = "preview." + name[-1]

	# download image
	image_url = image['file']['url']
	util.logger.info("Downloading preview image from Notion.")
	urllib.request.urlretrieve(
		image_url,
		os.path.join(util.NOTION_FOLDER, short_name, util.ASSETS, previewimage)
	)

	return previewimage

def fetch_favicon(post, short_name):
	# If the post has no emoji icon, return the default
	if post["icon"]["type"] != "emoji":
		return "favicon.png"
	
	# Get emoji name
	emoji = post['icon']["emoji"]
	if len(emoji) > 1:
		emoji = emoji[0]

	# Download emoji as png
	util.logger.info(f"Downloading emoji as favicon: {emoji}")
	urlretrieve(
		f"https://emojiapi.dev/api/v1/{hex(ord(emoji))[2:]}/32.png", 
		os.path.join(util.NOTION_FOLDER, short_name, util.ASSETS, "favicon.png")
	)

	return os.path.join(short_name, "favicon.png")

def format_tags(post):
	return str(post["properties"]["Tags"]["multi_select"])

def rss_tags(post):
	tags = []
	
	for tag in post["properties"]["Tags"]["multi_select"]:
		tags += [tag["name"]]

	return str(tags)

# Check if the post has the tag "Short"
def check_short(post):
	tags = post["properties"]["Tags"]["multi_select"]

	for tag in tags:
		if tag["name"] == "Short":
			return True
	
	return False

# Calculate time to read blog post
def get_words(text):
	minutes = round(len(text.split(" ")) / 200)

	if minutes > 1:
		return f"{minutes} minutes"
	
	return f"{minutes} minute"

def get_sourcecode(post):
	try:
		src = post["properties"]["sourcecode"]["rich_text"][0]["plain_text"]
		return f'"{src}"'
	except KeyError:
		return ""

def add_metadata(markdown_text, metadata):
	util.logger.info("Inserting jekyll metadata.")

	# Convert metadata dictionary to string
	def metadata_to_string(metadata):
		s = ""
		for key, value in metadata.items():
			s += f"{key}: {value}\n"

		return f"---\nlayout: page\n{s}---\n"

	return f"{metadata_to_string(metadata)}\n{markdown_text}"

# Replace single quote dollar sign with double dollar sign
def render_math(markdown_text):
	# Split text at code blocks to avoid replacing dollar signs
	code_pattern = re.compile(r'(```[\s\S]*?```|`[^`\n]*`)')
	split_text = code_pattern.split(markdown_text)

	# Regex pattern to detect single dollar sign math blocks
	math_pattern = re.compile(r"(?<!\$)\$([^$]+?)\$(?!\$)")

	# Replace the dollar signs
	output_text = []
	has_math = False
	for index, part in enumerate(split_text):
		# Check if text is inside or outside code block
		if index % 2 == 0:
			part, n_subs = math_pattern.subn(r"$$\1$$", part)

			# Check if any $ ... $ was replaced
			if n_subs > 0:
				has_math = True

		output_text += [part]

	if has_math:
		util.logger.info("Formatting inline equations.")
		markdown_text = ''.join(output_text)

	return has_math, markdown_text

def convert_image(short_name, path, filename, extension = "webp"):
	# Check if image already has desired extension
	src_extension = filename.split(".")[-1]
	if src_extension == extension:
		return path, filename

	# Open image with pillow and convert to rgb
	im = Image.open(path)
	rgb_im = im.convert('RGB')

	# Save path of image before conversion
	previous_image = path

	# Get new filename
	filename = ".".join(filename.split(".")[:-1]) + f".{extension}"
	path = os.path.join(util.NOTION_FOLDER, short_name, util.ASSETS, filename)

	# Save image as jpg with 99% quality
	util.logger.debug(f"Saving encoded image as {path}")
	rgb_im.save(path, quality=99)

	# Delete image
	os.remove(previous_image)

	return path, filename

def rename_image_to_hash(short_name, path, filename):
	import hashlib

	# Hash image usign MD5
	image_hash = hashlib.md5(
		open(path,'rb').read()
	).hexdigest()

	# Use it as filename
	filename = image_hash + ".webp"
	output_path = os.path.join(util.NOTION_FOLDER, short_name, util.ASSETS, filename)
	
	util.logger.debug(f"Renaming image to {output_path}")
	os.rename(path, output_path)

	return output_path, filename

def get_image_name_notion(page_images, image_n):
	image = page_images[image_n]["image"]

	if image["caption"]:
		return image["caption"][0]["plain_text"]

	return "Image illustrating the blog post."

def format_images(post_id, short_name, markdown_text, encode_images, rename_images, dst_extension):
	# Set image counter to 0
	global image_n
	image_n = 0
	# Get images from post
	global page_images
	page_images = notion_api.get_images(post_id)

	def replace_path(match):
		# Get image number variable
		global image_n
		global page_images

		# Get matches
		image_name = match.group(1)
		filename = match.group(2)
		after = match.group(3)
		caption = match.group(4)

		path = os.path.join(util.NOTION_FOLDER, short_name, util.ASSETS, filename)

		if encode_images:
			path, filename = convert_image(short_name, path, filename, extension=dst_extension)

		if rename_images:
			path, filename = rename_image_to_hash(short_name, path, filename)

		image_name = get_image_name_notion(page_images, image_n)

		# Increment image counter by 1
		image_n += 1

		util.logger.debug(f"Changing image tag for: ![{image_name}](/assets/{short_name}/{filename})")
		
		# Check if the text below the image is the caption as output by notion
		if image_name == caption:
			return f"![{image_name}](/assets/{short_name}/{filename})"
		
		return f"![{image_name}](/assets/{short_name}/{filename}){after}"

	util.logger.info("Replacing image tags in markdown with correct paths.")
	if encode_images:
		util.logger.info("Encode images to webp.")
	if rename_images:
		util.logger.info("Rename image to it's hash.")
	
	markdown_text = re.sub(
		r"\!\[([^\]]+)\]\(([^\)]+)\)(\n\n([^\n]+))?",
		replace_path,
		markdown_text
	)

	return markdown_text

def format_page(post_id, post, short_name, publish_time, filename, use_katex, encode_images = True, rename_images = True, dst_extension = "webp"):
	# Read file
	markdown_text = ""
	util.logger.debug("Reading .md file.")
	with open(os.path.join(util.NOTION_FOLDER, short_name, filename + ".md"), "r") as f:
		markdown_text = f.read()

	# Replace MD image tags with correct filename
	markdown_text = format_images(post_id, short_name, markdown_text, encode_images, rename_images, dst_extension)
	util.PBAR.update()

	# Ensure correct math rendering with katex
	if use_katex:
		has_math, markdown_text = render_math(markdown_text)
	else:
		has_math, _ = render_math(markdown_text)
	util.PBAR.update()

	# Set metadata
	metadata = {
		"title": f'"{post["properties"]["Name"]["title"][0]["text"]["content"]}"',
		"time": get_words(markdown_text),
		"published": publish_time,
		"colortags": format_tags(post),
		"tags": rss_tags(post),
		"permalink": short_name,
		"favicon": fetch_favicon(post, short_name),
		"excerpt": f'"{richtext_convertor(post["properties"]["Summary"]["rich_text"])}"',
		"short": check_short(post),
		"sourcecode": get_sourcecode(post),
		"math": has_math
	}

	# Get preview image for post
	previewimage = fetch_previewimage(post, short_name)
	if previewimage:
		metadata["image"] = os.path.join(util.ASSETS, short_name, previewimage)

	# insert jekyll metadata
	markdown_text = add_metadata(markdown_text, metadata)
	util.PBAR.update()

	util.logger.info("Output formatted markdown file.")
	with open(os.path.join(util.NOTION_FOLDER, short_name, filename + ".md"), "w") as f:
		f.write(markdown_text)
	util.PBAR.update()

	return

def export_page(post_id, post, use_katex, encode_images, rename_images, dst_extension):
	util.logger.info("Downloading markdown from Notion.")
	download_markdown(post_id)
	util.PBAR.update()

	# Get url name of the page
	short_name = post["properties"]["short-name"]["rich_text"][0]["text"]["content"]
	publish_time = post["properties"]["Date"]["date"]["start"].split("T")[0]
	filename = publish_time + "-" + short_name

	fs.extract_zip(post_id, short_name)
	util.PBAR.update()
	fs.clean_zip(post_id)

	rename_post_folder(post_id, short_name, filename)
	move_assets(short_name)
	util.PBAR.update()

	format_page(post_id, post, short_name, publish_time, filename, use_katex, encode_images, rename_images, dst_extension)

	fs.copy_post_to_blog(short_name, publish_time)
	util.PBAR.update()

	return
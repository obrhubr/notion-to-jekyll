# Notion to Jekyll

This script was written for my blog [obrhubr.org](https://obrhubr.org). I use a Github Action that runs daily which downloads the posts from Notion and updates my Github Pages site.

In order for this to work you will need to have a database in your Notion which contains the following attributes: (be careful, these are case-sensitive)
 - `Tags` (Multi-Select)
 - `Blog` (Multi-Select with either `Preview` or `Publish`)
 - `Date` (Date)
 - `Summary` (Text)
 - `preview-image` (Image)
 - `short-name` (Text)
 - `sourcecode` (Text)

The post will only be published if the `Blog` attribute is set to `Publish`.

![Notion Database containing the articles](.github/images/db.png)

![Post and all properties](.github/images/properties.png)

## Install

Download this repository and run

```bash
pip install .
```

You will no be able to call `notion-to-jekyll` from anywhere.

## Usage

The script expects a few arguments to run correctly.
You will have to provide the Notion API token that you have configured to be able to access the DB and the id of the DB. They will need to either be in a `.env` file in your blog's source folder:

```bash
NOTION_TOKEN=secret_test
DB_ID=test
```

Or they will need to be passed with the following command line options:

```bash
notion-to-jekyll --notion-token secret_test --db-id test
```

### Arguments:

Either call `notion-to-jekyll --help` or see the following table for **optional** arguments:

#### Arguments to add logging
| Option | Usage |
|-	|-	|
| `--log`	| Log updated posts to Logsnag, expects LOGSNAG_TOKEN env var.	|

#### Arguments to add logging
| Option | Usage |
|-	|-	|
| `--assets-folder`	| Use an alternative output folder for the assets.	|
| `--output-folder`	| Use an alternative output folder for the posts. |

#### Arguments to specify which posts to download

| Option | Usage |
|-	|-	|
| `--download-all` | Download all posts.	|
| `--update-time`	| Download only posts that have been updated in the last *t* seconds. |

#### Arguments that affect markdown formatting

| Option | Usage |
|-	|-	|
| `--use-katex`	| Use Katex formatting for equations.	|
| `--encode-jpg`	| Encode images as jpgs.	|
| `--rename-images`	| Rename images to a hash of their content.	|

## Acknowledgments

This could not have been possible without the great [notion2md](https://github.com/echo724/notion2md) library.
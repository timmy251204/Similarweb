from playwright.async_api import async_playwright
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, \
    CallbackQueryHandler, ContextTypes
import asyncio
import nest_asyncio
import re
from urllib.parse import urljoin
nest_asyncio.apply()
import os
from dotenv import load_dotenv
import logging


load_dotenv()
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
google_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
login_session_path = os.getenv("LOGIN_SESSION_PATH")




logging.basicConfig(level=logging.INFO)
logging.info("Starting crawler_tg script...")

async def setup_browser():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context(storage_state=login_session_path)
    page = await context.new_page()
    return browser, page, p



async def search_website_analysis(page, website, data, business_id):
    logging.info("step1")
    try:
        await page.goto("https://pro.similarweb.com/#/activation/setup", timeout=60000)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="debugstart.png", full_page=True)
        await asyncio.sleep(5)
    except Exception as e:
        logging.info("step1 failed")
        return None

    logging.info("step2")
    try:
        await page.screenshot(path="debug.png", full_page=True)
        await page.wait_for_selector("div[data-automation-icon-name='sidebar3-website-analysis']", timeout=20000)
        button = page.locator("div[data-automation-icon-name='sidebar3-website-analysis']")
        await button.click()
        await asyncio.sleep(5)
    except Exception as e:
        logging.info("step2 failed")
        return None
    search_input = page.locator(
        "input[data-automation-textfield='autocomplete']")
    await search_input.click()
    await search_input.fill(website)
    await asyncio.sleep(5)
    await page.keyboard.press("Enter")
    await asyncio.sleep(5)
    logging.info("setp3 end")
    # basic info
    # number
    try:
        element_number = page.locator("div[class^='TotalNumberStyled-']")
        number = await element_number.text_content()
    except:
        number = None
    # percentage change
    try:
        element_percentage = await page.wait_for_selector(
            'div.ChangeValue.ChangeValue--up.ChangeValue--', timeout=2000)
        percentage = await element_percentage.text_content()
        # print(element_percentage.text_content())
    except:
        try:
            element_percentage = await page.wait_for_selector(
                'div.ChangeValue.ChangeValue--down.ChangeValue--', timeout=2000)
            percentage = await element_percentage.text_content()
            # print(element_percentage.text_content())
        except:
            percentage = None
            # print("Element with specified classes not found.")

    # countries
    geography_button = page.locator("span[data-automation='secondary-item']",
                                    has_text="Geography")
    await geography_button.click()
    await asyncio.sleep(3)
    data_g = []
    try:
        for row in range(3):
            country_locator = page.locator(
                f"div[data-table-row='{row}'][data-automation-column-key='Country'] .country-text")
            country_name = await country_locator.get_attribute("title")

            min_value_locator = page.locator(
                f"div[data-table-row='{row}'][data-automation-column-key='Share'] span.min-value")
            min_value = await min_value_locator.inner_text() if min_value_locator else None

            if country_name and min_value:
                data_g.append(country_name)
                data_g.append(min_value)
    except:
        data_g = None
    # similiar websites
    similar_website_button = page.locator(
        "span[data-automation='secondary-item']", has_text="Similar Sites")
    await similar_website_button.click()
    await asyncio.sleep(3)
    try:
        for row in range(50):
            website_locator = page.locator(
                f"div[data-table-row='{row}'][data-automation-column-key='Domain'] a.cell-clickable")
            website_name = await website_locator.inner_text() if website_locator else None
            business_locator = page.locator(
                f"div[data-table-row='{row}'][data-automation-column-key='Category'] a.category-filter-cell")
            business_name = await business_locator.inner_text() if business_locator else None
            if website_name and (business_id in business_name):
                data.append(website_name)
    except:
        data = None
    #incoming traffic
    indata = []
    incoming_website_button = page.locator(
        "span[data-automation='secondary-item']", has_text="Incoming Traffic")
    await incoming_website_button .click()
    await asyncio.sleep(3)
    try:
        for row in range(50):
            incoming_locator = page.locator(
                f"div[data-table-row='{row}'][data-automation-column-key='Domain'] a.cell-clickable")
            incoming_name = await incoming_locator.inner_text() if incoming_locator else None
            indata.append(incoming_name)
    except:
        indata = None
    #outgoing traffic
    outdata = []
    outgoing_website_button = page.locator(
        "span[data-automation='secondary-item']", has_text="Outgoing Traffic")
    await outgoing_website_button .click()
    await asyncio.sleep(3)
    try:
        for row in range(50):
            outgoing_locator = page.locator(
                f"div[data-table-row='{row}'][data-automation-column-key='Domain'] a.cell-clickable")
            outgoing_name = await outgoing_locator.inner_text() if outgoing_locator else None
            outdata.append(outgoing_name)
    except:
        outdata = None
    #outgoing traffic
    # print(data_websites)
    return number, percentage, data_g, indata, outdata


async def create_excel(email, name):
    json_key_path = google_credentials

    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(json_key_path, scopes=scope)
    client = gspread.authorize(creds)

    # Open an existing Google Sheet by title
    spreadsheet = client.create(name)

    # Select the first worksheet
    worksheet = spreadsheet.get_worksheet(0)

    # Sample data to upload
    table_line = [
        ["Website", "Last month increase", "Percentage", "Geography", " Inflow", "Outflow"]
    ]

    # Upload data (starting from cell A1)
    worksheet.update(range_name="A1", values=table_line)

    # Set up your credentials and authenticate with Google Drive API
    scope = ["https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(
        google_credentials,
        scopes=scope)
    drive_service = build("drive", "v3", credentials=creds)

    # Define the permissions for your email
    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": email
    }

    # File ID of the Google Sheet you want to share
    file_id = spreadsheet.id

    # Share the spreadsheet
    drive_service.permissions().create(
        fileId=file_id,
        body=permission,
        fields="id"
    ).execute()

    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": "tablegeneratorsafe@gmail.com"
    }

    file_id = spreadsheet.id

    # Share the spreadsheet
    drive_service.permissions().create(
        fileId=file_id,
        body=permission,
        fields="id"
    ).execute()


    return worksheet, spreadsheet.url


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Use /setemail <email> to set your email, /setspreadsheet <spreadsheet name> to set your spreadsheet name, /category to choose genre of search and /crawl <website> to start crawling.")


async def set_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Please provide an email after the /setemail command.")
        return
    context.user_data['email'] = context.args[0]
    await update.message.reply_text(f"Email set to: {context.args[0]}, please type /setspreadsheet Name of your table")


async def set_spreadsheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Please provide a spreadsheet name after the /setspreadsheet command.")
        return
    context.user_data['spreadsheet_name'] = context.args[0]
    await update.message.reply_text(
        f"Spreadsheet name set to: {context.args[0]}, type /category function next")


async def crawl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(start_crawl(update, context))


async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Gambling", callback_data='Gambling')],
        [InlineKeyboardButton("Casinos", callback_data='Casinos')],
        [InlineKeyboardButton("Sports Betting", callback_data='Sports Betting')],
        [InlineKeyboardButton("Lottery", callback_data='Lottery')],
        [InlineKeyboardButton("Poker", callback_data='Poker')],
        [InlineKeyboardButton("Bingo", callback_data='Bingo')],
        [InlineKeyboardButton("Other gambling", callback_data='Gambling - Other')],
        [InlineKeyboardButton("Porno", callback_data='Adult')]




    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose a category:",
                                    reply_markup=reply_markup)


# Function to handle the button press
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Store the selected category in user_data
    context.user_data['category'] = query.data
    await query.edit_message_text(text=f"Category selected: {query.data}, please type /crawl name of your website next")


async def start_crawl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only initial setup code
    start_website = context.args[0]
    category = context.user_data['category']
    worksheet, spreadsheet_url = await create_excel(context.user_data['email'],
                                                    context.user_data[
                                                        'spreadsheet_name'])
    await update.message.reply_text(f"Spreadsheet created: {spreadsheet_url}")
    asyncio.create_task(
        run_crawl_process(update, worksheet, start_website, category))








async def run_crawl_process(update: Update, worksheet, start_website, category):
    browser, page, p = await setup_browser()
    websites = [start_website]
    solved = set()


    try:
        while websites:

            website = websites.pop(0)
            if website in solved:
                continue
            increase, percent, country, inflow, outflow = await search_website_analysis(page,
                                                                                        website,
                                                                                        websites,
                                                                                        category)

            try:
                country_str = ", ".join(country) if country else None
            except:
                country_str = None
            try:
                inflow_str = ", ".join(inflow) if inflow else None
            except:
                inflow_str = None
            try:
                outflow_str = ", ".join(outflow) if outflow else None
            except:
                outflow_str = None
            worksheet.append_row([website, increase, percent, country_str, inflow_str, outflow_str])
            solved.add(website)


        await update.message.reply_text(f"Crawl completed, for {start_website}")
    finally:
        await browser.close()
        await p.stop()



websites = []
solved = []


async def main():
    app = ApplicationBuilder().token(telegram_bot_token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setemail", set_email))
    app.add_handler(CommandHandler("setspreadsheet", set_spreadsheet))
    app.add_handler(CommandHandler("category", category))
    app.add_handler(CommandHandler("crawl", start_crawl))
    # app.add_handler(CommandHandler("analyze_links", analyze_links))

    # Callback query handler for category selection
    app.add_handler(CallbackQueryHandler(button))

    print("Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())


    # Run the bot application within the current event loop

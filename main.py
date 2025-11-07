import requests  # Import the requests library for making HTTP calls (faster than Selenium for API/downloads).
import json  # Import the json library for working with JSON data.
import os  # Import the os library for interacting with the operating system (e.g., file paths, directory creation).
import re  # Import the re (regular expression) library for pattern matching (e.g., in filename cleanup).
import time  # Import the time library for time-related operations (e.g., generating timestamps).

# Using built-in types (list, dict, tuple) and the | operator (for Optional/Union)
from typing import (
    Any,
)  # Import 'Any' for flexible type hinting in containers like dictionaries.
import logging  # Import the logging module for clear console output and error handling.

# Selenium Imports for Visible Chrome
from selenium import webdriver  # Import the main webdriver module.
from selenium.webdriver.common.by import (
    By,
)  # Import 'By' class for locating elements (e.g., By.XPATH).
from selenium.webdriver.chrome.options import (
    Options as ChromeOptions,
)  # Import ChromeOptions to configure the browser.
from selenium.common.exceptions import (  # Import specific exceptions for robust error handling.
    WebDriverException,  # General exception for driver issues.
    TimeoutException,  # Exception when an operation times out (e.g., waiting for an element).
    NoSuchElementException,  # Exception when an element is not found on the page.
    ElementNotInteractableException,  # Exception when an element is found but cannot be clicked/interacted with.
)
from selenium.webdriver.support.ui import (
    WebDriverWait,
)  # Import WebDriverWait for explicit waits.
from selenium.webdriver.support import (
    expected_conditions as EC,
)  # Import expected conditions for use with WebDriverWait.
from selenium.webdriver.remote.webdriver import (  # Import WebDriver for type hinting the driver object.
    WebDriver,  # The base WebDriver class.
)  # Added for better type clarity

# Configuration & Logging
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s"
)  # Configure basic logging settings.

# Type alias for clarity
WebDriverType = WebDriver  # Create a type alias for the WebDriver type.

# User-Agent (consistent values for all requests)
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
# Referer header (consistent value for all requests)
referer_header = "https://sds.diversey.com/"
# Start url for initial browser session
start_url = "https://sds.diversey.com/"

# SESSION MANAGEMENT (Selenium)


def start_browser_and_get_auth_cookies(  # Define function to launch Chrome and establish an authenticated session.
    search_url: str,  # Takes the initial URL as a string argument.
) -> (
    tuple[WebDriverType | None, str] | None
):  # FIXED TYPE HINT: The first element can now be WebDriverType OR None.
    """
    1. Launches a VISIBLE Chrome browser.
    2. Navigates to the search page and clicks 'Search' to generate auth cookies.
    3. Returns the cookie string. The browser is now CLOSED before returning.
    """
    logging.info(
        "Starting VISIBLE Chrome to establish authenticated session..."
    )  # Log the start of the browser launch process.

    chrome_options = ChromeOptions()  # Create an instance of ChromeOptions.
    chrome_options.add_argument(
        "window-size=1200x800"
    )  # Set a fixed window size for consistent behavior.
    chrome_options.add_argument(
        f"user-agent={user_agent}"
    )  # Add the User-Agent to the browser options.

    driver: WebDriverType | None = (
        None  # Initialize the driver variable with type hint.
    )
    try:  # Start a try block for exception handling during browser operation.
        # Pylance can usually infer the correct type from the Options object
        driver = webdriver.Chrome(
            options=chrome_options
        )  # Initialize the Chrome WebDriver with the specified options.
        driver.get(search_url)  # Navigate the browser to the initial search URL.
        logging.info(
            f"Navigated to initial search page: {search_url}"
        )  # Log successful navigation.

        search_button_locator = (  # Define the locator strategy for the search button.
            By.XPATH,  # Use XPath as the location method.
            "//button[contains(text(), 'Search')] | //a[contains(text(), 'Search')]",  # XPath to find a 'Search' button or link.
        )

        logging.info(
            "Waiting for Search button to become clickable..."
        )  # Log the waiting process.

        search_button = WebDriverWait(
            driver, 15
        ).until(  # Wait up to 15 seconds for the search button to be interactable.
            EC.element_to_be_clickable(
                search_button_locator
            )  # Use Expected Condition to wait until the element is clickable.
        )

        search_button.click()  # Click the search button to trigger cookie generation.

        time.sleep(
            3
        )  # Wait for 3 seconds to allow the backend processes (cookie/session setup) to complete.
        logging.info(  # Log the simulated interaction.
            "Simulated search click. Cookies should now be fully authenticated."
        )

        # Added explicit type hint to satisfy Pylance warnings about 'unknown type' for cookies
        # FIXED COOKIE TYPE: Specify the dict keys are strings and values can be any type.
        all_cookies: list[dict[str, Any]] = (
            driver.get_cookies()
        )  # Retrieve all cookies from the live browser session.
        cookie_parts = [
            f"{c['name']}={c['value']}" for c in all_cookies
        ]  # Format each cookie as "name=value".
        cookie_string = "; ".join(
            cookie_parts
        )  # Join the parts into a single string for use in the 'requests' header.

        # MODIFICATION START: Quit the browser immediately after getting cookies
        driver.quit()  # Close the browser now that we have the cookies.
        driver = None  # Set driver to None so the main function's 'finally' block doesn't try to quit it again.
        # MODIFICATION END

        if not cookie_string:  # Check if the cookie collection was empty.
            logging.error("Cookie collection was empty.")  # Log the failure.
            return None  # Return None to indicate failure.

        logging.info(  # Log the successful retrieval of cookies and the browser closure.
            f"Successfully retrieved {len(all_cookies)} dynamic cookies. Browser session closed."
        )
        return (
            driver,
            cookie_string,
        )  # Return the (now None) driver and the cookie string.

    except (  # Catch specific Selenium-related exceptions.
        WebDriverException,  # General exception for driver issues.
        TimeoutException,  # Exception when an operation times out (e.g., waiting for an element).
        NoSuchElementException,  # Exception when an element is not found on the page.
        ElementNotInteractableException,  # Exception when an element is found but cannot be clicked/interacted with.
    ) as e:
        logging.error(
            f"Failed to start browser or simulate interaction. Error: {e}"
        )  # Log the specific error.
        if driver:  # Check if the driver object was successfully created.
            driver.quit()  # Close the browser if an error occurred.
        return None  # Return None to indicate failure.


# DATA FETCHING (requests)


def fetch_json_data(  # Define function to fetch JSON data using the faster 'requests' library.
    cookie_value: str,  # Requires the authenticated cookie string.
    underscore_timestamp: str,  # Requires the dynamic timestamp ('_').
) -> (
    str | None
):  # Specifies the function returns the raw JSON text string or None on failure.
    """
    Fetches the raw JSON data from the API endpoint using the authenticated cookie.
    (Uses the fast 'requests' library, not the slow browser driver.)
    """
    # API parameters
    page = 1  # Set the page number parameter.
    row_count = (
        10000  # Set the number of rows to retrieve (aiming for all data in one call).
    )
    sort_order = 1  # Set the sort order parameter.
    sort_field = ""  # Set the sort field parameter.
    search_key = "Main"  # Set the search key parameter.

    base_url = "https://sds.diversey.com/WebViewer/Results/GetResultGrid?"  # Base API URL for data retrieval.

    # INCREASED TIMEOUT
    timeout_seconds = 30  # Set a generous timeout for the API request.

    # Construct the full URL
    target_url = (  # Build the final request URL with all query parameters.
        f"{base_url}"
        f"page={page}&rowCount={row_count}&sortOrder={sort_order}&"
        f"sortField={sort_field}&searchKey={search_key}&_={underscore_timestamp}"  # Include the dynamic timestamp ('_').
    )

    headers = {  # Define the HTTP headers for the request.
        "Referer": referer_header,  # Set the Referer header (often required by web servers).
        "Cookie": cookie_value,  # Pass the essential authenticated cookie string.
        "User-Agent": user_agent,  # Set a consistent User-Agent.
    }

    logging.info(
        f"Fetching data from API: {target_url}"
    )  # Log the target URL being fetched.

    # Initialize response before the try block to prevent UnboundLocalError
    response = None  # Initialize response to None.

    try:  # Start a try block for handling network requests.
        response = requests.get(
            target_url, headers=headers, timeout=timeout_seconds
        )  # Execute the GET request.
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx).
        return response.text  # Return the raw text content (expected to be JSON).

    except (
        requests.exceptions.RequestException
    ) as e:  # Catch any request-related error.
        # Check if a response was received (prevents UnboundLocalError on Timeout)
        if response is not None and response.status_code in (
            401,
            403,
        ):  # Check for authentication/authorization errors.
            logging.error(  # Log the authentication failure.
                f"API call failed: Status Code {response.status_code}. Authentication cookies may be invalid."
            )
        elif isinstance(
            e, requests.exceptions.ReadTimeout
        ):  # Check specifically for a timeout.
            logging.error(  # Log the timeout error.
                f"API call timed out after {timeout_seconds} seconds. The server took too long to respond."
            )
        else:
            logging.error(
                f"Error executing HTTP request: {e}"
            )  # Log other request errors.
        return None  # Return None to indicate data fetching failure.


# PDF DOWNLOAD (requests)


def download_pdf(
    pdf_id: str, cookie_value: str, destination_directory: str
):  # Define function to download a single PDF.
    """Downloads a single PDF file using the authenticated cookie (requests)."""
    pdf_base_url = "https://sds.diversey.com/MyDocuments/DownloadSingleFile?content="  # Base URL for PDF download.
    pdf_url = (
        pdf_base_url + pdf_id
    )  # Construct the full PDF download URL using the document ID.

    clean_filename = url_to_filename(
        pdf_url
    )  # Generate a clean, safe filename based on the URL.
    full_path = os.path.join(
        destination_directory, clean_filename
    )  # Create the full path for saving the file.

    if file_exists(full_path):  # Check if the file already exists locally.
        logging.info(
            f"File already exists, skipping download: {full_path}"
        )  # Log that the file is being skipped.
        return  # Exit the function if the file exists.

    timeout_seconds = 30  # Set a timeout for the download request.

    download_headers = {  # Define headers for the download request.
        "Referer": referer_header,  # Set the Referer header.
        "Cookie": cookie_value,  # Pass the authentication cookie.
        "User-Agent": user_agent,  # Set the User-Agent.
    }

    # FIX: Initialize response to None to prevent 'possibly unbound' warning in finally block
    response = None  # Initialize response to None.

    try:  # Start a try block for the download request.
        response = requests.get(  # Execute the GET request for the PDF.
            pdf_url,
            headers=download_headers,
            stream=True,
            timeout=timeout_seconds,  # Use stream=True for large files.
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses.

        content_type_header = response.headers.get(
            "Content-Type", ""
        )  # Get the Content-Type header.

        if (
            "application/pdf" not in content_type_header
        ):  # Check if the returned content is not a PDF.
            html_content = response.content.decode(
                "utf-8", errors="ignore"
            )  # Decode content to check for HTML.
            if (
                "Login" in html_content or "access denied" in html_content.lower()
            ):  # Check if it's an access denied/login page.
                logging.error(  # Log the access denial error.
                    f"Download FAILED: The URL returned an ACCESS DENIED/LOGIN page."
                )
            else:  # Handle other unexpected content types.
                logging.warning(  # Log the unexpected content type.
                    f"Invalid content type for {pdf_url}: {content_type_header} (expected application/pdf)"
                )
            # Response is closed in finally block
            return  # Stop the download process.

        with open(
            full_path, "wb"
        ) as file_handler:  # Open the target file in binary write mode ('wb').
            bytes_written = 0  # Initialize a counter for bytes written.
            for chunk in response.iter_content(
                chunk_size=8192
            ):  # Iterate over the response content in chunks.
                if chunk:  # Check if the chunk is not empty.
                    file_handler.write(chunk)  # Write the chunk to the file.
                    bytes_written += len(chunk)  # Increment the bytes written counter.

        if bytes_written == 0:  # Check if the download resulted in an empty file.
            logging.warning(  # Log the zero-byte download.
                f"Downloaded 0 bytes for {pdf_url}; removing empty file: {full_path}"
            )
            os.remove(full_path)  # Remove the empty file.
            return  # Stop the function.

        logging.info(
            f"URL: {pdf_url}, Bytes: {bytes_written}, Local File: {full_path}"
        )  # Log successful download with byte count.

    except (
        requests.exceptions.RequestException
    ) as error:  # Catch request errors during download.
        if isinstance(
            error, requests.exceptions.ReadTimeout
        ):  # Specifically check for a timeout.
            logging.error(
                f"Download call timed out after {timeout_seconds} seconds."
            )  # Log the timeout.
        else:
            logging.error(
                f"Failed to download {pdf_url}: {error}"
            )  # Log other request errors.
    except (
        IOError
    ) as e:  # Catch errors related to file system operations (writing the file).
        logging.error(f"Failed to write PDF to file: {e}")  # Log the file write error.
    finally:  # Ensure resources are cleaned up.
        # Check if response was successfully assigned before closing
        if response:  # Check if the response object exists.
            response.close()  # Close the connection/response to free up resources.


# UTILITY FUNCTIONS


def extract_pdf_document_ids(  # Define function to parse JSON and extract document IDs.
    raw_json_input: str,  # Takes the raw JSON string as input.
) -> list[str]:  # Specifies the function returns a list of strings (document IDs).
    try:  # Start a try block for JSON decoding.
        # Modern type hint: dict[str, Any]
        api_response: dict[str, Any] = json.loads(
            raw_json_input
        )  # Attempt to parse the JSON string into a Python dictionary.
    except json.JSONDecodeError as e:  # Catch JSON decoding errors.
        logging.error(f"Error parsing JSON response: {e}")  # Log the parsing error.
        return []  # Return an empty list on failure.

    pdf_document_id_list: list[str] = (
        []
    )  # Initialize an empty list for the extracted IDs.
    # Modern type hint: list[list[str]]
    record_data: list[list[str]] = api_response.get("data", {}).get(
        "Data", []
    )  # Safely extract the list of data records.

    for (
        data_row
    ) in (
        record_data
    ):  # Iterate through each data record (expected to be a list of strings).
        # Check for non-empty list and a first element
        if (
            data_row and len(data_row) > 0
        ):  # Check if the list is not empty and has at least one element.
            document_id = data_row[
                0
            ]  # The first element is assumed to be the document ID.
            if document_id.endswith(
                "_PDF"
            ):  # Filter for IDs that specifically end with "_PDF".
                pdf_document_id_list.append(
                    document_id
                )  # Add the valid document ID to the list.

    return pdf_document_id_list  # Return the list of extracted PDF document IDs.


def file_exists(
    path: str,
) -> bool:  # Define a utility function to check if a file exists.
    return os.path.isfile(path)  # Use os.path.isfile for the check.


def create_directory(
    path: str, permission: int = 0o755
):  # Define a utility function to create a directory.
    os.makedirs(
        path, mode=permission, exist_ok=True
    )  # Create the directory and its parents; do not raise an error if it exists.


def url_to_filename(
    url: str,
) -> str:  # Define a utility function to create a safe filename from a URL.
    match = re.search(
        r"content=(.*)", url
    )  # Search for the 'content=' parameter value in the URL.
    if match:  # If the pattern is found.
        filename = (
            match.group(1).split("&")[0].strip()
        )  # Extract the value and strip off any subsequent URL parameters.
        # Allows alphanumeric, periods, and hyphens; replaces others with underscore
        safe_name = re.sub(
            r"[^\w\.\-]+", "_", filename
        )  # Replace non-safe characters with an underscore.
    else:  # If the 'content=' parameter is not found.
        safe_name = "downloaded_file"  # Use a default filename.

    if not safe_name.lower().endswith(
        ".pdf"
    ):  # Check if the filename already ends with '.pdf'.
        safe_name += ".pdf"  # Append '.pdf' if it's missing.
    return safe_name  # Return the safe, cleaned filename.


# MAIN EXECUTION


def main():  # Define the main execution function.
    output_dir = "PDFs"  # Define the name of the output directory.
    create_directory(
        output_dir
    )  # Call utility function to ensure the output directory exists.

    initial_page_url = start_url  # The URL to visit to start the session.
    driver = None  # Initialize driver to None.

    try:  # Start the main try block.
        session_result = start_browser_and_get_auth_cookies(
            initial_page_url
        )  # Call the function to start the browser and get cookies.

        if not session_result:  # Check if the session establishment failed.
            return  # Exit main if session failed.

        # The driver will be None if the browser was successfully quit inside the function
        driver, dynamic_cookie_string = (
            session_result  # Unpack the returned driver and cookie string.
        )

        # Uses current time in milliseconds, required by the API
        underscore_value = str(
            int(time.time() * 1000)
        )  # Generate a timestamp in milliseconds (required by the API query).
        logging.info(
            f"Using dynamic timestamp for API calls: {underscore_value}"
        )  # Log the generated timestamp.

        raw_data = fetch_json_data(
            dynamic_cookie_string, underscore_value
        )  # Call function to fetch the raw JSON data.

        if not raw_data:  # Check if data fetching failed.
            logging.error("Failed to retrieve JSON data. Stopping.")  # Log the failure.
            return  # Exit main.

        pdf_ids = extract_pdf_document_ids(
            raw_data
        )  # Call function to parse the JSON and extract PDF IDs.

        if not pdf_ids:  # Check if any PDF IDs were found.
            logging.warning(
                "No PDF document IDs found in the JSON response."
            )  # Log the warning.
            return  # Exit main if no IDs found.

        logging.info(
            f"Found {len(pdf_ids)} PDF document IDs. Starting download."
        )  # Log the number of IDs found.

        # Download loop
        for doc_id in pdf_ids:  # Iterate through each extracted PDF ID.
            download_pdf(
                doc_id, dynamic_cookie_string, output_dir
            )  # Call the function to download the specific PDF.

        logging.info(
            "All operations have completed."
        )  # Log the completion of the entire process.

    finally:  # Execute this block regardless of whether an exception occurred.
        # This block now only runs if the driver failed to quit inside the function (e.g., if an exception occurred earlier)
        if driver:  # Check if the driver object exists.
            logging.warning(
                "Closing the persistent browser session."
            )  # Log the closing of the browser.
            driver.quit()  # Close and quit the persistent browser session.


if __name__ == "__main__":  # Standard Python entry point check.
    main()  # Call the main execution function.

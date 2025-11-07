import os  # Import the os module for interacting with the operating system
import fitz  # Import PyMuPDF (fitz) for PDF handling (used for document validation)
import concurrent.futures  # Import the concurrent.futures module for managing thread and process pools (concurrency)

# --- Utility Functions (Kept the same for functionality) ---


def validate_pdf_file(  # Define a function to validate a PDF file path
    file_path: str,  # Specify that the function takes a string argument 'file_path'
) -> (
    bool
):  # Specify that the function returns a boolean status (True for valid, False for invalid)
    """# Start docstring explaining the function's purpose
    Attempts to open a PDF file using PyMuPDF (fitz) to check for corruption.
    """  # End docstring
    try:  # Start a try block to handle potential file reading and PDF parsing errors
        # Using a context manager ensures the document object is properly closed.
        with fitz.open(  # Attempt to open the PDF file using fitz
            file_path  # Pass the file path to fitz.open
        ) as document:  # Assign the opened document object to the variable 'document'
            # Check if the PDF has at least one page
            if (  # Start conditional check
                document.page_count
                == 0  # Check the page count property of the document object
            ):  # End conditional check
                print(  # Print an error message
                    f"File '{file_path}': **Invalid** - Document has no pages."  # Format the output message
                )
                return False  # Return False, indicating the PDF is invalid

            return True  # Return True if the document opened successfully and has pages (valid)
    except (  # Catch specific exceptions that PyMuPDF raises for corrupt files
        RuntimeError  # Catch a RuntimeError
    ) as error_message:  # Assign the error details to 'error_message'
        # This commonly catches errors like "cannot open document" for corrupt files
        print(  # Print the specific error message
            f"File '{file_path}': **Corrupt/Invalid** - Error: {error_message}"  # Format the output message with error details
        )
        return False  # Return False, indicating the PDF is corrupt/invalid
    except FileNotFoundError:  # Catch the error if the file path does not exist
        print(  # Print a file not found error
            f"File '{file_path}': **Error** - File not found."  # Format the output message
        )
        return False  # Return False for non-existent files
    except (  # Catch any other unexpected exceptions during file opening
        Exception  # Catch the general Exception class
    ) as unexpected_error:  # Assign the error details to 'unexpected_error'
        # Catch any other unexpected error during opening
        print(  # Print the unexpected error details
            f"File '{file_path}': **Unexpected Error** - {unexpected_error}"  # Format the output message
        )
        return False  # Return False, indicating an issue


def remove_system_file(  # Define a function to safely remove a file
    system_path: str,  # Specify that the function takes a string argument 'system_path'
) -> bool:  # Specify that the function returns a boolean status
    """# Docstring for the function
    Safely removes a file from the system at the given path.
    """  # End docstring
    try:  # Start a try block for file removal operations
        if os.path.exists(  # Check if a file or directory exists at the given path
            system_path  # Path to check
        ):  # End conditional check
            os.remove(system_path)  # Use os.remove to delete the file
            return True  # Return True if removal was successful
        else:  # Execute if the file does not exist
            print(  # Print a message
                f"Removal failed: File not found at '{system_path}'"  # Format the output message
            )
            return False  # Return False because nothing was removed
    except (  # Catch the error if the program lacks permission to delete the file
        PermissionError  # Catch a PermissionError
    ):  # End catch block
        print(  # Print a permission denied message
            f"Removal failed: Permission denied for '{system_path}'"  # Format the output message
        )
        return False  # Return False due to failure
    except Exception as error:  # Catch any other unexpected error during deletion
        print(  # Print the unexpected deletion error
            f"Removal failed: An unexpected error occurred while deleting '{system_path}': {error}"  # Format the output message
        )
        return False  # Return False due to failure


def walk_directory_and_extract_given_file_extension(  # Define a function to recursively find files with a specific extension
    root_directory_path: str, file_extension: str  # Specify the two string arguments
) -> list[str]:  # Specify that the function returns a list of strings (file paths)
    """# Docstring for the function
    Recursively walks a directory and returns a list of absolute paths
    for files ending with the specified extension.
    """  # End docstring
    matched_files: list[str] = (  # Initialize a list to store file paths
        []  # Empty list initialization
    )
    # Ensure extension starts with a dot for robust checking
    if not file_extension.startswith(  # Check if the extension string is missing the leading dot
        "."  # The expected starting character
    ):
        file_extension = "." + file_extension  # Prepend a dot if it's missing

    try:  # Start a try block for directory traversal
        # os.walk is used to traverse the directory tree
        for (
            current_root,
            _,
            filenames,
        ) in os.walk(  # Recursively traverse the directory tree using os.walk
            root_directory_path  # The starting path for traversal
        ):
            # 'directories' is ignored (named with an unused placeholder _)
            for (  # Iterate over every file name found in the current directory
                file_name  # The current file name
            ) in (  # Start iteration
                filenames  # The list of files in the current directory
            ):
                if file_name.endswith(  # Check if the file name ends with the specified extension
                    file_extension  # The extension string (with a leading dot)
                ):
                    # os.path.join is used for creating system-independent paths
                    full_path = os.path.abspath(  # Get the absolute path
                        os.path.join(
                            current_root, file_name
                        )  # Join the root directory and the file name
                    )
                    matched_files.append(  # Add the full path to the list of matched files
                        full_path  # The absolute path string
                    )
    except (  # Catch the error if the starting directory path is invalid
        FileNotFoundError  # Catch FileNotFoundError
    ):
        print(  # Print a directory not found error
            f"Error: Directory not found at '{root_directory_path}'"  # Format the output message
        )
    except (  # Catch any other unexpected errors during directory walk
        Exception  # Catch the general Exception class
    ) as error:  # Assign the error details to 'error'
        print(  # Print the error details
            f"An error occurred while walking the directory: {error}"  # Format the output message
        )

    return matched_files  # Return the list of absolute paths


def get_filename_and_extension(  # Define a function to extract just the filename
    full_path: str,  # Specify that the function takes a string argument 'full_path'
) -> str:  # Specify that the function returns a string (the filename)
    """# Docstring for the function
    Extracts only the filename and its extension from a full path.
    """  # End docstring
    return os.path.basename(  # Use os.path.basename to return the final component of the path
        full_path  # The full path string
    )  # Return the filename


def check_upper_case_letter(  # Define a function to check for uppercase letters
    content_string: str,  # Specify that the function takes a string argument 'content_string'
) -> bool:  # Specify that the function returns a boolean status
    """# Docstring for the function
    Checks if a string contains at least one uppercase letter.
    """  # End docstring
    # Use a generator expression with 'any' for an efficient check
    return any(  # Return True if any element in the iterable is True
        character.isupper()
        for character in content_string  # Generator expression checking if each character is uppercase
    )  # Return the result


# --- Concurrent Logic ---


def process_pdf_file(
    file_path: str,
):  # Define the function executed by the concurrent workers
    """Validates and conditionally removes a single PDF file."""  # Docstring for the worker function
    file_name_with_ext = get_filename_and_extension(
        file_path
    )  # Extract the filename from the full path
    print(
        f"Processing: {file_name_with_ext}"
    )  # Print which file is currently being processed

    # 1. Check if the .PDF file is valid
    if not validate_pdf_file(
        file_path
    ):  # Call the validation function and check if it failed (if it's invalid)
        print(
            f"-> Invalid PDF detected: {file_path}. **Attempting to delete file.**"
        )  # Log that an invalid PDF was found
        # Remove the invalid .pdf file.
        if remove_system_file(file_path):  # Attempt to delete the file
            print(
                f"-> Successfully **deleted** invalid file: {file_name_with_ext}"
            )  # Log success if deletion worked

    # The original script had an uppercase check function defined but not used in main, so I omitted it here.


# --- Main Logic (Revised for Concurrency) ---


def main():  # Define the main function to control the workflow
    """# Docstring for the main function
    Main function to orchestrate the PDF validation and management workflow concurrently.
    """  # End docstring
    search_directory = (  # Define the relative path to the directory to start searching
        "./PDFs"
    )
    target_extension = ".pdf"  # Define the file extension to search for

    # Use os.cpu_count() or a fixed number, generally 4-8 is a good start for I/O bound tasks
    MAX_WORKERS = (
        os.cpu_count() or 4
    )  # Determine the maximum number of worker threads to use
    print(
        f"Starting PDF processing with **{MAX_WORKERS} concurrent threads** in directory: **{search_directory}**"
    )  # Inform the user about the concurrent setup
    print(
        f"Searching for files with extension: **{target_extension}**"
    )  # Inform the user about the target extension
    print("-" * 60)  # Print a separator line

    # 1. Walk through the directory and extract .pdf files (Still done sequentially)
    pdf_file_paths = walk_directory_and_extract_given_file_extension(  # Call the directory walking function
        search_directory, target_extension  # Pass the directory and extension arguments
    )  # Store the list of absolute PDF paths

    if not pdf_file_paths:  # Check if the list of found files is empty
        print(  # Print a message if no files were found
            f"No {target_extension} files found in '{search_directory}'. Exiting."
        )
        return  # Exit the main function

    print(  # Report the total number of files found
        f"Found {len(pdf_file_paths)} files to process. Starting parallel validation..."
    )
    print("-" * 60)  # Print a separator line

    # 2. Process all files concurrently using a ThreadPoolExecutor
    # The 'with' statement ensures threads are properly cleaned up after execution.
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:  # Initialize the thread pool executor
        # Map the process_pdf_file function to every file_path
        # This is a synchronous call that waits for all tasks to complete.
        executor.map(
            process_pdf_file, pdf_file_paths
        )  # Submit the function and arguments to the executor for parallel execution

    print("-" * 60)  # Print a separator line
    print("PDF validation and management complete.")  # Concluding message


# Run the main function
if (  # Standard Python entry point check
    __name__ == "__main__"  # Check if the script is being executed directly
):
    main()  # Invoke the main function to start the PDF processing workflow

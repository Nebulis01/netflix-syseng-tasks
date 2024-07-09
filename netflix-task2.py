import os.path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

#netflix
source_folderid = '1cpo-7jgKSMdde-QrEJGkGxN1QvYdzP9V'

# If modifying these scopes, delete the file token.json.
# For this usecase we only need access to drive metadata per google api doc
# https://developers.google.com/drive/api/guides/api-specific-auth
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


# Authenticate and authorize the user
creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first time.
# pathing may need to be updated depending on execution environment
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json')
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'yourapiclientsecretgoeshere.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

# Build the Google Drive API service caller
service = build('drive', 'v3', credentials=creds)

def count_files_and_folders(service, source_folderid):
    file_count = 0
    folder_count = 0

    # Call the Drive v3 API to list files and folders in the specified folder
    results = service.files().list(
        q=f"'{source_folderid}' in parents",
        spaces='drive',
        fields='files(id, name, mimeType)',
        pageToken=None
    ).execute()

    items = results.get('files', [])

    if items:
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursively count files and folders in subfolders
                subfile_count, subfolder_count = count_files_and_folders(service, item['id'])
                file_count += subfile_count
                folder_count += 1 + subfolder_count  # count current folder and its contents
            else:
                file_count += 1

    return file_count, folder_count
    
def generate_report(service, source_folderid):
    # Call the Drive v3 API to list top-level folders under the source folder
    results = service.files().list(
        q=f"'{source_folderid}' in parents and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)',
        pageToken=None
    ).execute()

    items = results.get('files', [])

    if items:
        total_nested_folders = 0

        for item in items:
            folder_id = item['id']
            folder_name = item['name']

            # Count child objects recursively for this top-level folder
            file_count, folder_count = count_files_and_folders(service, folder_id)
            total_nested_folders += folder_count

            print(f"Folder '{folder_name}':")
            print(f"  - Number of files: {file_count}")
            print(f"  - Number of folders (including nested): {folder_count}")
            print()

        print(f"Total number of nested folders for source folder: {total_nested_folders}")

    else:
        print('No folders found.')

file_count, folder_count = count_files_and_folders(service, source_folderid)


print()
print(f'Source Folder ID: {source_folderid}')
print()
print('Showing recursive results for the source folder')
print(f'Number of folders: {folder_count}')
print(f'Number of files: {file_count}')
print()
generate_report(service, source_folderid)
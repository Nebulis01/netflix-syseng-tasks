import os.path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
# For this usecase we need full access to drive
# https://developers.google.com/drive/api/guides/api-specific-auth
SCOPES = ['https://www.googleapis.com/auth/drive']

#netflix
source_folderid = '1cpo-7jgKSMdde-QrEJGkGxN1QvYdzP9V'
#personal
destination_folderid = '1FLioo0FxvSLIQG-SnIDJ0h5EXDI6jj31'

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
            'yourapiclientsecretgoeshere.json.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

# Build the Google Drive API service caller
service = build('drive', 'v3', credentials=creds)

def copy_folder_contents(service, source_folderid, destination_folderid):
    # Call the Drive v3 API to list files and folders in the source folder
    results = service.files().list(
        q=f"'{source_folderid}' in parents",
        spaces='drive',
        fields='files(id, name, mimeType)',
        pageToken=None
    ).execute()

    items = results.get('files', [])

    if items:
        for item in items:
            item_id = item['id']
            item_name = item['name']
            item_type = item['mimeType']

            # Create a copy of the item in the destination folder
            file_metadata = {
                'name': item_name,
                'parents': [destination_folderid]
            }

            if item_type == 'application/vnd.google-apps.folder':
                # Create a new folder in the destination if it doesn't exist
                new_folder = service.files().create(
                    body={
                        'name': item_name,
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [destination_folderid]
                    },
                    fields='id'
                ).execute()

                # Recursively copy contents of this folder to the newly created folder
                copy_folder_contents(service, item_id, new_folder['id'])
            else:
                # If the item is a file, copy it to the destination folder
                service.files().copy(fileId=item_id, body=file_metadata).execute()

            print(f"Copied '{item_name}'")

    else:
        print('No items found in the source folder.')

# Copy contents of source folder to destination folder
copy_folder_contents(service, source_folderid, destination_folderid)
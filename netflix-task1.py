import os.path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

netflix_source_folder = '1cpo-7jgKSMdde-QrEJGkGxN1QvYdzP9V'

#build the query for the API list call, using f string because Python is fun
query_netflix = f"'{netflix_source_folder}' in parents"


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

# Build the Google Drive API service
service = build('drive', 'v3', credentials=creds)

# Call the Drive v3 API to list files and folders in root
results = service.files().list(
    q=query_netflix,
    spaces='drive',
    fields='files(id, name, mimeType), nextPageToken',
    pageToken=None
).execute()

items = results.get('files', [])
    

#look a the results and parse out the mimeType for folders in google drive, increment counter for folders and assume all other items are files, increment as required
if not items:
    print('No files or folders found.')
else:
    file_count = 0
    folder_count = 0
    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            folder_count += 1
        else:
            file_count += 1

print()
print(f'Source Folder ID: {netflix_source_folder}')
print()
print('Showing non recursive results for the source folder')
print(f'Number of folders: {folder_count}')
print(f'Number of files: {file_count}')

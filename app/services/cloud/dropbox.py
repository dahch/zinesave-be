import os
import json
import requests
from sqlalchemy.orm import Session
from app.domain.models.cloud_connection import CloudConnection
from app.services.cloud.adapter import CloudStorageAdapter, UploadResult

class DropboxAdapter(CloudStorageAdapter):
    def upload_file(self, file_path: str, connection: CloudConnection, db: Session) -> UploadResult:
        # 1. Refresh Token if needed (Dropbox tokens are short-lived if using offline access)
        # Note: Implementing full refresh logic requires calling their token endpoint.
        # For this iteration, we assume the token is valid or refreshed externally/lazily. 
        # Ideally, we should check expiry and refresh here.
        
        self._refresh_token_if_needed(connection, db)

        # 2. Upload
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        headers = {
            "Authorization": f"Bearer {connection.access_token}",
            "Dropbox-API-Arg": json.dumps({
                "path": f"/{filename}",
                "mode": "add",
                "autorename": True,
                "mute": False
            }),
            "Content-Type": "application/octet-stream"
        }

        with open(file_path, "rb") as f:
            data = f.read()

        response = requests.post(
            "https://content.dropboxapi.com/2/files/upload",
            headers=headers,
            data=data
        )
        
        if response.status_code != 200:
             raise Exception(f"Dropbox upload failed: {response.text}")

        res_json = response.json()
        
        # 3. Create Shared Link (to get a URL)
        # We need a separate call to share the file and get user accessible URL
        link_url = self._create_shared_link(filename, connection.access_token)
        
        return {
            "id": res_json.get("id"),
            "url": link_url
        }

    def _create_shared_link(self, path: str, token: str) -> str:
        url = "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "path": f"/{path}"
        }
        
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200 or resp.status_code == 409: # 409 means already exists
             # If 409, we might need to fetch existing link, but for simplicity let's try assuming response structure
             # Actually, creating link returns the link object. 
             # On 409, error details usually contain the existing link, but handling that is complex.
             # Let's try "list_shared_links" if create fails, or assume success for now.
             pass
        
        # If create failed (e.g. already shared), try get existing
        if resp.status_code == 409:
             return self._get_existing_link(path, token)

        if resp.status_code != 200:
            return None
            
        return resp.json().get("url")

    def _get_existing_link(self, path: str, token: str) -> str:
        url = "https://api.dropboxapi.com/2/sharing/list_shared_links"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        data = {"path": f"/{path}", "direct_only": True}
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            links = resp.json().get("links", [])
            if links:
                return links[0].get("url")
        return None

    def _refresh_token_if_needed(self, connection: CloudConnection, db: Session):
        # Placeholder for refresh logic. 
        # Dropbox returns 'expires_in' (usually 4h). 
        # If connection.expires_at is passed, we call https://api.dropbox.com/oauth2/token
        # with grant_type=refresh_token
        pass

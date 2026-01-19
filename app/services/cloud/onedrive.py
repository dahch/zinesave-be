import os
import requests
from sqlalchemy.orm import Session
from app.domain.models.cloud_connection import CloudConnection
from app.services.cloud.adapter import CloudStorageAdapter, UploadResult

class OneDriveAdapter(CloudStorageAdapter):
    def upload_file(self, file_path: str, connection: CloudConnection, db: Session) -> UploadResult:
        # 1. Refresh Token
        self._refresh_token_if_needed(connection, db)

        filename = os.path.basename(file_path)
        
        # 2. Upload to Root (PUT /me/drive/root:/{filename}:/content)
        url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{filename}:/content"
        
        with open(file_path, "rb") as f:
            data = f.read()
            
        headers = {
            "Authorization": f"Bearer {connection.access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        response = requests.put(url, headers=headers, data=data)
        
        if response.status_code not in (200, 201):
            raise Exception(f"OneDrive upload failed: {response.text}")
            
        res_json = response.json()
        
        # 3. Create Sharing Link (optional, but good for uniformity)
        # MS Graph returns 'webUrl' in the response which is the View Link. 
        # We can use that directly or create a specific sharing link.
        # "webUrl" is usually accessible if the user is logged in, but for public/app usage maybe we want createLink.
        # Let's start with webUrl which is easiest.
        
        return {
            "id": res_json.get("id"),
            "url": res_json.get("webUrl")
        }

    def _refresh_token_if_needed(self, connection: CloudConnection, db: Session):
        # Placeholder for Refresh Logic
        # MS Graph tokens expire in 1h approx.
        pass

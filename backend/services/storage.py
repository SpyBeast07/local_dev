import boto3
import json
import os
import socket
from botocore.config import Config
from botocore.exceptions import EndpointConnectionError, NoCredentialsError, PartialCredentialsError
from typing import List, Dict, Any, Optional
import mimetypes
from services.docker import get_containers, get_container_details

SOURCES_FILE = "sources.json"

class StorageService:
    @staticmethod
    def _load_sources() -> List[Dict[str, Any]]:
        if not os.path.exists(SOURCES_FILE):
            return []
        try:
            with open(SOURCES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def _save_sources(sources: List[Dict[str, Any]]):
        with open(SOURCES_FILE, "w") as f:
            json.dump(sources, f, indent=4)

    @classmethod
    def get_client(cls, source_id: str):
        sources = cls._load_sources()
        source = next((s for s in sources if s["id"] == source_id), None)
        if not source:
            raise ValueError(f"Source with id {source_id} not found")

        return boto3.client(
            's3',
            endpoint_url=source["endpoint"],
            aws_access_key_id=source["access_key"],
            aws_secret_access_key=source["secret_key"],
            region_name=source["region"],
            config=Config(signature_version='s3v4')
        )

    @classmethod
    def list_buckets(cls, source_id: str):
        try:
            client = cls.get_client(source_id)
            response = client.list_buckets()
            return [
                {
                    "name": bucket["Name"],
                    "created_at": bucket["CreationDate"].isoformat() if bucket["CreationDate"] else None
                }
                for bucket in response.get("Buckets", [])
            ]
        except EndpointConnectionError:
            raise Exception("Could not connect to the storage endpoint. Please check if your MinIO/S3 server is running.")
        except Exception as e:
            raise e

    @classmethod
    def create_bucket(cls, source_id: str, bucket_name: str):
        client = cls.get_client(source_id)
        client.create_bucket(Bucket=bucket_name)
        return {"success": True}

    @classmethod
    def delete_bucket(cls, source_id: str, bucket_name: str):
        client = cls.get_client(source_id)
        client.delete_bucket(Bucket=bucket_name)
        return {"success": True}

    @classmethod
    def list_objects(cls, source_id: str, bucket_name: str, prefix: str = ""):
        client = cls.get_client(source_id)
        response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        objects = []
        for obj in response.get("Contents", []):
            name = obj["Key"]
            mime_type, _ = mimetypes.guess_type(name)
            objects.append({
                "name": name,
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
                "type": mime_type or "application/octet-stream"
            })
            
        return objects

    @classmethod
    def upload_object(cls, source_id: str, bucket_name: str, file_content: bytes, file_name: str):
        client = cls.get_client(source_id)
        client.put_object(Bucket=bucket_name, Key=file_name, Body=file_content)
        return {"success": True}

    @classmethod
    def delete_object(cls, source_id: str, bucket_name: str, object_name: str):
        client = cls.get_client(source_id)
        client.delete_object(Bucket=bucket_name, Key=object_name)
        return {"success": True}

    @classmethod
    def detect_local_storage(cls) -> List[Dict[str, Any]]:
        suggestions = []
        
        # 1. Scan Docker Containers
        containers = get_containers()
        if not isinstance(containers, dict) or "error" not in containers:
            for c in containers:
                is_minio = "minio" in c.get("image", "").lower() or "minio" in c.get("name", "").lower()
                if is_minio:
                    details = get_container_details(c["id"])
                    ports = details.get("NetworkSettings", {}).get("Ports", {}) if details else {}
                    for c_port, host_bindings in ports.items():
                        if host_bindings and "9000" in c_port:
                            host_port = host_bindings[0].get("HostPort")
                            suggestions.append({
                                "name": f"Local MinIO ({c['name']})",
                                "endpoint": f"http://localhost:{host_port}",
                                "type": "minio",
                                "detected_via": "docker"
                            })

        # 2. Scan Common Ports if not already found
        common_ports = [9000, 9001]
        for port in common_ports:
            endpoint = f"http://localhost:{port}"
            if any(s["endpoint"] == endpoint for s in suggestions):
                continue
                
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    suggestions.append({
                        "name": f"Local Storage (Port {port})",
                        "endpoint": endpoint,
                        "type": "s3",
                        "detected_via": "port_scan"
                    })
        
        return suggestions

    @classmethod
    def get_object(cls, source_id: str, bucket_name: str, object_name: str):
        client = cls.get_client(source_id)
        response = client.get_object(Bucket=bucket_name, Key=object_name)
        return response["Body"].read(), response["ContentType"]

    @classmethod
    def get_presigned_url(cls, source_id: str, bucket_name: str, object_name: str, download: bool = False):
        client = cls.get_client(source_id)
        params = {'Bucket': bucket_name, 'Key': object_name}
        if download:
            filename = object_name.split('/')[-1]
            from urllib.parse import quote
            params['ResponseContentDisposition'] = f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quote(filename)}"
        
        url = client.generate_presigned_url('get_object', Params=params, ExpiresIn=3600)
        return url

    @classmethod
    def add_source(cls, name: str, endpoint: str, access_key: str, secret_key: str, region: str = "us-east-1"):
        sources = cls._load_sources()
        import uuid
        new_source = {
            "id": str(uuid.uuid4()),
            "name": name,
            "endpoint": endpoint,
            "access_key": access_key,
            "secret_key": secret_key,
            "region": region
        }
        sources.append(new_source)
        cls._save_sources(sources)
        return new_source

    @classmethod
    def get_sources(cls):
        return cls._load_sources()

    @classmethod
    def delete_source(cls, source_id: str):
        sources = cls._load_sources()
        sources = [s for s in sources if s["id"] != source_id]
        cls._save_sources(sources)
        return {"success": True}
